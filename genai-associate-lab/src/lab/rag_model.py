"""RAG chain as a pyfunc model, logged with MLflow "models from code".

Exam §4: "Code a chain using a pyfunc model with pre- and post-processing",
"model flavor, embedding model, retriever, dependencies, input example, signature",
"control access to resources from model serving endpoints".

Flow:  input -> [PRE: validate, guardrails, normalise] -> retrieve -> prompt
       -> LLM -> [POST: mask PII, attach citations] -> output
"""
from __future__ import annotations

import mlflow
import pandas as pd
from mlflow.models import ModelConfig, set_model
from mlflow.pyfunc import PythonModel

from lab import guardrails

DEFAULT_CONFIG = {
    "llm_endpoint": "databricks-meta-llama-3-3-70b-instruct",
    "vs_endpoint": "genai_lab_vs",
    "index_name": "workspace.genai_lab.doc_chunks_index",
    "num_results": 4,
    "query_type": "HYBRID",
    "system_prompt": (
        "You are the Nimbus Cloud support assistant. Answer ONLY from the context. "
        "If the context does not contain the answer, say you don't know. "
        "Cite sources as [doc_id]. Be concise."
    ),
}


class RagModel(PythonModel):
    def __init__(self):
        self.cfg = None

    # ---- lifecycle -----------------------------------------------------
    def load_context(self, context):
        self._init()

    def _init(self):
        from databricks.sdk import WorkspaceClient

        self.cfg = {**DEFAULT_CONFIG, **(ModelConfig(development_config=DEFAULT_CONFIG).to_dict())}
        # Inside Model Serving, credentials come from the *resources* declared at
        # log time (automatic authentication passthrough) -- no tokens in code.
        self.llm = WorkspaceClient().serving_endpoints.get_open_ai_client()
        try:
            from databricks.ai_search.client import VectorSearchClient
        except ImportError:  # pragma: no cover
            from databricks.vector_search.client import VectorSearchClient
        self.index = VectorSearchClient(disable_notice=True).get_index(
            endpoint_name=self.cfg["vs_endpoint"], index_name=self.cfg["index_name"])

    # ---- PRE-processing -----------------------------------------------
    @staticmethod
    def _extract_question(model_input) -> str:
        if isinstance(model_input, pd.DataFrame):
            model_input = model_input.to_dict(orient="records")[0]
        if isinstance(model_input, dict):
            if "question" in model_input:
                return str(model_input["question"])
            if "messages" in model_input:
                return str(model_input["messages"][-1]["content"])
        raise ValueError("Expected {'question': str} or {'messages': [...]}")

    # ---- core ----------------------------------------------------------
    @mlflow.trace(span_type="RETRIEVER", name="retrieve")
    def _retrieve(self, question: str) -> list[dict]:
        res = self.index.similarity_search(
            query_text=question, columns=["chunk_id", "doc_id", "text"],
            num_results=self.cfg["num_results"], query_type=self.cfg["query_type"])
        cols = [c["name"] for c in res["manifest"]["columns"]]
        return [dict(zip(cols, row)) for row in res["result"]["data_array"]]

    @mlflow.trace(span_type="LLM", name="generate")
    def _generate(self, question: str, docs: list[dict]) -> str:
        context = "\n\n".join(f"[{d['doc_id']}] {d['text']}" for d in docs)
        resp = self.llm.chat.completions.create(
            model=self.cfg["llm_endpoint"], temperature=0.0, max_tokens=400,
            messages=[
                {"role": "system", "content": self.cfg["system_prompt"]},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ])
        return resp.choices[0].message.content

    @mlflow.trace(name="rag_predict")
    def predict(self, context, model_input, params=None):
        if self.cfg is None:
            self._init()
        question = self._extract_question(model_input)

        pre = guardrails.check_input(question)                      # PRE
        if not pre.allowed:
            return {"answer": guardrails.REFUSAL, "sources": [], "blocked": pre.reasons}

        docs = self._retrieve(pre.text)
        answer = self._generate(pre.text, docs)
        post = guardrails.check_output(answer)                      # POST
        return {
            "answer": post.text,
            "sources": sorted({d["doc_id"] for d in docs}),
            "blocked": [],
        }


set_model(RagModel())
