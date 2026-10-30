"""Tool-calling support agent on MLflow's ResponsesAgent interface.

Exam §1/§3/§4: define & order tools for multi-stage reasoning, MLflow + Agent
Framework, tracing. The loop is deliberately manual (no LangGraph) so every step
of "LLM decides -> tool runs -> result fed back" is visible. Notebook 07 contrasts
this with a LangGraph version.
"""
from __future__ import annotations

import json
import uuid
from typing import Generator

import mlflow
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

LLM_ENDPOINT = "databricks-meta-llama-3-3-70b-instruct"
VS_ENDPOINT = "genai_lab_vs"
INDEX_NAME = "workspace.genai_lab.doc_chunks_index"

PLAN_PRICING = {  # USD, per month / included requests / per extra 1k requests
    "free": (0, 10_000, None),
    "pro": (49, 500_000, 0.20),
    "enterprise": (499, 10_000_000, 0.08),
}

SYSTEM_PROMPT = (
    "You are the Nimbus Cloud support agent. Use tools to ground every factual "
    "answer. Order of work: (1) search_docs for policy/limits, (2) calculate_overage "
    "when the user asks about cost, (3) answer and cite doc ids like [billing_policy]. "
    "Never invent prices."
)

TOOLS = [
    {"type": "function", "function": {
        "name": "search_docs",
        "description": "Search the Nimbus Cloud knowledge base. Use for policies, limits, security, onboarding.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Natural-language search query"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "calculate_overage",
        "description": "Compute the monthly bill for a plan given requests used. Use for any cost question.",
        "parameters": {"type": "object", "properties": {
            "plan": {"type": "string", "enum": list(PLAN_PRICING)},
            "requests_used": {"type": "integer", "minimum": 0}},
            "required": ["plan", "requests_used"]}}},
]


def calculate_overage(plan: str, requests_used: int) -> dict:
    """Pure function -> trivially unit-testable (Exam: test individual agent components)."""
    base, included, per_1k = PLAN_PRICING[plan.lower()]
    extra = max(0, requests_used - included)
    if extra and per_1k is None:
        return {"plan": plan, "status": "blocked", "note": "Free plan is hard-capped; upgrade required."}
    overage = round(extra / 1000 * (per_1k or 0), 2)
    return {"plan": plan, "base_usd": base, "extra_requests": extra,
            "overage_usd": overage, "total_usd": round(base + overage, 2)}


class SupportAgent(ResponsesAgent):
    def __init__(self):
        # Clients are created lazily so the module imports (and unit-tests) off-platform.
        self._client = None
        self._index = None

    @property
    def client(self):
        if self._client is None:
            from databricks.sdk import WorkspaceClient

            self._client = WorkspaceClient().serving_endpoints.get_open_ai_client()
        return self._client

    @property
    def index(self):
        if self._index is None:
            try:
                from databricks.ai_search.client import VectorSearchClient
            except ImportError:  # pragma: no cover
                from databricks.vector_search.client import VectorSearchClient
            self._index = VectorSearchClient(disable_notice=True).get_index(
                endpoint_name=VS_ENDPOINT, index_name=INDEX_NAME)
        return self._index

    @mlflow.trace(span_type="TOOL", name="search_docs")
    def _search_docs(self, query: str) -> str:
        res = self.index.similarity_search(
            query_text=query, columns=["doc_id", "text"], num_results=4, query_type="HYBRID")
        rows = res["result"]["data_array"]
        return "\n\n".join(f"[{r[0]}] {r[1]}" for r in rows) or "No results."

    @mlflow.trace(span_type="TOOL", name="calculate_overage")
    def _calc(self, plan: str, requests_used: int) -> str:
        return json.dumps(calculate_overage(plan, requests_used))

    def _run_tool(self, name: str, args: dict) -> str:
        if name == "search_docs":
            return self._search_docs(**args)
        if name == "calculate_overage":
            return self._calc(**args)
        return f"Unknown tool {name}"

    # ResponsesAgent auto-traces predict, so no @mlflow.trace decorator here.
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        outputs, messages = [], [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in request.input:
            messages.append({"role": getattr(item, "role", "user"), "content": item.content
                             if isinstance(item.content, str) else str(item.content)})

        for _ in range(5):  # hard cap on reasoning steps = cost + runaway control
            resp = self.client.chat.completions.create(
                model=LLM_ENDPOINT, messages=messages, tools=TOOLS, temperature=0.0)
            msg = resp.choices[0].message
            if not msg.tool_calls:
                outputs.append(self.create_text_output_item(msg.content or "", id=str(uuid.uuid4())))
                break
            messages.append({"role": "assistant", "content": msg.content or "",
                             "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                outputs.append(self.create_function_call_item(
                    id=str(uuid.uuid4()), call_id=tc.id, name=tc.function.name,
                    arguments=tc.function.arguments or "{}"))
                result = self._run_tool(tc.function.name, args)
                outputs.append(self.create_function_call_output_item(call_id=tc.id, output=result))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        return ResponsesAgentResponse(output=outputs)

    def predict_stream(self, request: ResponsesAgentRequest
                       ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        for item in self.predict(request).output:
            yield ResponsesAgentStreamEvent(type="response.output_item.done", item=item)


set_model(SupportAgent())
