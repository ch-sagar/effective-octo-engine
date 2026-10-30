# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 4 — Measure retrieval *before* adding an LLM
# MAGIC **Goal:** compute hit-rate / recall / MRR on the golden set and decide which chunking + query mode is better, with numbers.
# MAGIC
# MAGIC **Why:** when a RAG answer is wrong, 80% of the time retrieval failed. Test retrieval alone so you know where to look.
# MAGIC
# MAGIC **Exam link:** §2 tools & metrics to evaluate retrieval, advanced chunking · §3 select chunking strategy based on retrieval evaluation.

# COMMAND ----------
# MAGIC %pip install -q databricks-ai-search mlflow>=3
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, mlflow, pandas as pd
sys.path.append(os.path.abspath("../src"))
from lab import config as C
from lab.compat import get_vs_client
from lab.metrics import evaluate_retriever
mlflow.set_experiment(C.EXPERIMENT_PATH)
vsc = get_vs_client()
gold = spark.table(C.EVAL_TABLE).toPandas()
gold = gold[gold.expected_docs.apply(len) > 0]          # drop the injection test (no expected doc)
print(len(gold), "answerable questions")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 4.1 — Run the retriever on every question
# MAGIC We compare 4 configurations: {markdown, fixed} × {ANN, HYBRID}. Dedupe doc ids while preserving rank — we score *documents*, not chunks.

# COMMAND ----------
def run(index_name, query_type, k=5):
    idx = vsc.get_index(C.VS_ENDPOINT, index_name)
    rows = []
    for _, r in gold.iterrows():
        res = idx.similarity_search(query_text=r.question, columns=["doc_id"], num_results=k, query_type=query_type)
        ranked = [x[0] for x in res["result"]["data_array"]]
        seen, uniq = set(), []
        for d in ranked:
            if d not in seen: seen.add(d); uniq.append(d)
        rows.append({"retrieved": uniq, "relevant": list(r.expected_docs)})
    return rows

configs = {"markdown+ANN": (C.INDEX_NAME, "ANN"), "markdown+HYBRID": (C.INDEX_NAME, "HYBRID"),
           "fixed+ANN": (C.INDEX_FIXED_NAME, "ANN"), "fixed+HYBRID": (C.INDEX_FIXED_NAME, "HYBRID")}
results = []
for name, (iname, qt) in configs.items():
    with mlflow.start_run(run_name=f"retrieval-{name}"):
        m = evaluate_retriever(run(iname, qt), k=3)
        mlflow.log_params({"config": name}); mlflow.log_metrics({k: v for k, v in m.items() if k != "n"})
        results.append({"config": name, **m})
display(pd.DataFrame(results).sort_values("mrr", ascending=False))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 4.2 — Read the failures, don't just read the averages
# MAGIC Pick the best config and print the questions where the right doc was NOT rank 1.

# COMMAND ----------
best = max(results, key=lambda r: r["mrr"])["config"]
iname, qt = configs[best]
for row, (_, g) in zip(run(iname, qt), gold.iterrows()):
    if not row["retrieved"] or row["retrieved"][0] not in row["relevant"]:
        print("❌", g.question, "→ got", row["retrieved"][:3], "wanted", row["relevant"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 4
# MAGIC - [ ] Four MLflow runs with `hit_rate@3`, `recall@3`, `mrr`
# MAGIC - [ ] You can say, in one sentence, which config won and **why** (e.g. header-aware chunks keep the plan name next to the number)
# MAGIC - [ ] You've looked at ≥1 failing question and can guess the cause
# MAGIC
# MAGIC ### Exercise
# MAGIC Add 5 questions of your own to `golden_eval` (a Delta table — `INSERT INTO`). Re-run. Evaluation sets are living assets.
