# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 0 — Set up your workspace
# MAGIC **Goal:** a schema, a Volume with the sample documents, and proof that the Foundation Model API answers.
# MAGIC
# MAGIC **Why this matters:** every later stage reads/writes `workspace.genai_lab.*`. If names are wrong here, everything breaks later.
# MAGIC
# MAGIC **Exam link:** §4 Unity Catalog three-level namespace, Volumes, Foundation Model APIs.
# MAGIC
# MAGIC ### Before you run this
# MAGIC 1. Sign up at **databricks.com/learn/free-edition**.
# MAGIC 2. Workspace → *Create* → **Git folder** → paste the URL of your copy of this repo (or *Import* the zip).
# MAGIC 3. Open this notebook, attach **Serverless** compute (the only option in Free Edition).

# COMMAND ----------
# MAGIC %pip install -q databricks-ai-search mlflow>=3 databricks-sdk pypdf beautifulsoup4 databricks-agents databricks-langchain
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys
sys.path.append(os.path.abspath("../src"))
from lab import config as C
print("catalog:", C.CATALOG, "| schema:", C.SCHEMA, "| volume:", C.VOLUME_PATH)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 0.1 — Create the schema and Volume
# MAGIC A **Volume** is Unity Catalog's governed place for *files* (PDFs, HTML). A **table** is for rows. Raw documents go in a Volume; chunks go in a Delta table.

# COMMAND ----------
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {C.CATALOG}.{C.SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {C.CATALOG}.{C.SCHEMA}.{C.VOLUME}")
display(spark.sql(f"SHOW VOLUMES IN {C.CATALOG}.{C.SCHEMA}"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 0.2 — Copy the sample documents into the Volume
# MAGIC The Git folder lives in the workspace filesystem; Volumes are separate storage, so we copy.

# COMMAND ----------
import shutil, glob
src_dir = os.path.abspath("../data/raw")
for f in glob.glob(f"{src_dir}/*"):
    shutil.copy(f, C.VOLUME_PATH)
display(dbutils.fs.ls(C.VOLUME_PATH))

# COMMAND ----------
# Upload the two small CSV/JSONL helper files as Delta tables too
import pandas as pd
lic = pd.read_csv("../data/source_licenses.csv")
spark.createDataFrame(lic).write.mode("overwrite").saveAsTable(C.LICENSE_TABLE)
gold = pd.read_json("../data/golden_eval.jsonl", lines=True)
gold["expected_docs"] = gold["expected_docs"].apply(list)
spark.createDataFrame(gold).write.mode("overwrite").saveAsTable(C.EVAL_TABLE)
display(spark.table(C.EVAL_TABLE))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 0.3 — Which models do I actually have?
# MAGIC Free Edition exposes pay-per-token **Foundation Model APIs**. Names change, so list them rather than trusting the config.

# COMMAND ----------
from lab.compat import list_foundation_endpoints, chat
eps = list_foundation_endpoints()
display(pd.DataFrame(eps))

# COMMAND ----------
# MAGIC %md
# MAGIC If `C.LLM_ENDPOINT` or `C.EMBEDDING_ENDPOINT` is **not** in the table above, set an environment variable or edit `src/lab/config.py` now (also `LLM_ENDPOINT` in `src/lab/agent.py` and `rag_model.py`).

# COMMAND ----------
print(chat([{"role": "user", "content": "Reply with exactly: READY"}], model=C.LLM_ENDPOINT))

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 0
# MAGIC - [ ] Volume listing shows 7 files
# MAGIC - [ ] `golden_eval` table has 16 rows
# MAGIC - [ ] The last cell printed `READY`
# MAGIC
# MAGIC ### Common errors
# MAGIC | Symptom | Cause / fix |
# MAGIC |---|---|
# MAGIC | `PERMISSION_DENIED` creating schema | You're in the wrong catalog — run `SHOW CATALOGS` and set `LAB_CATALOG` |
# MAGIC | `ENDPOINT_NOT_FOUND` | Model name changed — use one from the table in 0.3 |
# MAGIC | `REQUEST_LIMIT_EXCEEDED` / 429 | Free-tier token limits — wait a minute, reduce `max_tokens` |
# MAGIC | `ModuleNotFoundError: lab` | Notebook isn't inside the Git folder, so `../src` doesn't exist |
