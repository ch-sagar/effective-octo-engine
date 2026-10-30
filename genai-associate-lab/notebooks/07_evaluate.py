# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 7 — Evaluate the agent with MLflow judges and custom scorers
# MAGIC **Goal:** run the golden set through the agent, score with LLM judges + your own code scorers, and read the results.
# MAGIC
# MAGIC **Exam link:** §6 MLflow scoring/tracing, judges needing ground truth, custom scorers, SME feedback, evaluation vs monitoring.
# MAGIC
# MAGIC ### Which judges need ground truth?
# MAGIC | Needs `expectations` | Does NOT need |
# MAGIC |---|---|
# MAGIC | Correctness, Equivalence, RetrievalSufficiency | Safety, RelevanceToQuery, RetrievalGroundedness, RetrievalRelevance, Guidelines |

# COMMAND ----------
# MAGIC %pip install -q databricks-ai-search mlflow>=3 databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, mlflow
sys.path.append(os.path.abspath("../src"))
from lab import config as C
mlflow.set_experiment(C.EXPERIMENT_PATH)
mlflow.openai.autolog()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 7.1 — Build the dataset in MLflow's format
# MAGIC Each record: `inputs` (what you send), `expectations` (ground truth).

# COMMAND ----------
gold = spark.table(C.EVAL_TABLE).toPandas()
data = [{"inputs": {"question": r.question},
         "expectations": {"expected_response": r.expected_response, "expected_docs": list(r.expected_docs)}}
        for r in gold.itertuples() if len(r.expected_docs) > 0]
print(len(data), "records")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 7.2 — `predict_fn`
# MAGIC Evaluate wants a function taking the keys in `inputs`. We call our RAG pyfunc (Stage 5) — swap in the agent later and compare.
# MAGIC Retrieval judges need spans of type **RETRIEVER** in the trace — our `rag_model.py` already creates one.

# COMMAND ----------
from lab.rag_model import RagModel
rag = RagModel(); rag._init()
def predict_fn(question: str):
    return rag.predict(None, {"question": question})

# COMMAND ----------
from mlflow.genai.scorers import Correctness, RelevanceToQuery, RetrievalGroundedness, Safety, Guidelines
from lab.scorers import cites_a_source, no_pii_leak, retrieved_expected_doc, concise

scorers = [
    Correctness(), RelevanceToQuery(), RetrievalGroundedness(), Safety(),
    Guidelines(name="no_guessing", guidelines="If the answer is not in the context the response must say it does not know instead of inventing facts."),
    cites_a_source, no_pii_leak, retrieved_expected_doc, concise,
]
results = mlflow.genai.evaluate(data=data, predict_fn=predict_fn, scorers=scorers)
display(results.tables["eval_results"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 7.3 — Read it like an engineer
# MAGIC Open *Experiments → Evaluation runs*. Sort by `correctness`. For each failure click through to the **trace** and answer:
# MAGIC - Did retrieval fail (wrong chunks)? → fix chunking/index (Stage 2–4)
# MAGIC - Did generation fail with the right chunks? → fix the prompt/model
# MAGIC - Did the *judge* mis-grade? → refine the guideline or add expected facts
# MAGIC
# MAGIC ## Step 7.4 — Close the loop with prompt change
# MAGIC Make `DEFAULT_CONFIG["system_prompt"]` stricter, re-run Step 7.2–7.3, and compare the two evaluation runs side by side. **This compare-runs workflow is the single most valuable habit in GenAI engineering.**
# MAGIC
# MAGIC ## Step 7.5 — Subject-matter-expert feedback (Review App)
# MAGIC SMEs label real traces without touching code. Needs a paid workspace for the full UI; the API is shown for completeness.

# COMMAND ----------
try:
    from mlflow.genai.labeling import create_labeling_session
    session = create_labeling_session(name="sme_review_1", assigned_users=[], label_schemas=None)
    print("labeling session created:", session)
except Exception as e:
    print("Review App / labeling not available in this workspace:", str(e)[:200])

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 7
# MAGIC - [ ] Evaluation run with 15 rows and ~9 metric columns
# MAGIC - [ ] You identified at least one failure and classified it (retrieval / generation / judge)
# MAGIC - [ ] You can explain why `Correctness` needs `expected_response` but `Safety` doesn't
# MAGIC
# MAGIC ### Evaluation vs monitoring (exam)
# MAGIC **Evaluation** = offline, fixed dataset, before release, compares versions. **Monitoring** = online, live traffic, no ground truth, detects drift/regressions after release (Stage 8).
