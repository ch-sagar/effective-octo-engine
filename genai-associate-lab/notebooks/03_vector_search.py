# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 3 — Build a Vector Search index and query it
# MAGIC **Goal:** endpoint → Delta Sync index (managed embeddings) → similarity, hybrid and filtered queries.
# MAGIC
# MAGIC **Exam link:** §4 create & query a Vector Search index · key concepts · configure for embeddings count/update frequency/latency/cost · §2 re-ranking.
# MAGIC
# MAGIC **Free Edition limits:** ONE endpoint, ONE search unit, **Delta Sync only** (no Direct Vector Access). Also the SDK is being renamed *AI Search* — our `compat.py` handles both.
# MAGIC
# MAGIC ### Concepts you must be able to explain
# MAGIC | Concept | Meaning |
# MAGIC |---|---|
# MAGIC | Endpoint | Compute that serves one or more indexes |
# MAGIC | Delta Sync index | Index auto-syncs from a Delta table (needs Change Data Feed) |
# MAGIC | Managed embeddings | You supply text; Databricks calls the embedding endpoint for you |
# MAGIC | `TRIGGERED` vs `CONTINUOUS` | Sync on demand (cheap) vs near-real-time (costly) |
# MAGIC | `ANN` vs `HYBRID` | Vector only vs vector + keyword (BM25-style), fused |

# COMMAND ----------
# MAGIC %pip install -q databricks-ai-search
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, time
sys.path.append(os.path.abspath("../src"))
from lab import config as C
from lab.compat import get_vs_client
vsc = get_vs_client()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.1 — Create the endpoint (takes ~5–10 min the first time ☕)

# COMMAND ----------
existing = [e["name"] for e in vsc.list_endpoints().get("endpoints", [])]
if C.VS_ENDPOINT not in existing:
    vsc.create_endpoint_and_wait(name=C.VS_ENDPOINT, endpoint_type="STANDARD", verbose=True)
print("endpoint ready:", C.VS_ENDPOINT)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.2 — Create the index
# MAGIC `primary_key` uniquely identifies a chunk. `embedding_source_column` is the text to embed. `columns_to_sync` are returned at query time (metadata).

# COMMAND ----------
def make_index(index_name, source_table):
    try:
        return vsc.create_delta_sync_index_and_wait(
            endpoint_name=C.VS_ENDPOINT, index_name=index_name, source_table_name=source_table,
            pipeline_type="TRIGGERED", primary_key="chunk_id",
            embedding_source_column="text", embedding_model_endpoint_name=C.EMBEDDING_ENDPOINT,
            columns_to_sync=["chunk_id", "doc_id", "section", "text", "strategy"], verbose=True)
    except Exception as e:
        if "already exists" in str(e).lower():
            idx = vsc.get_index(C.VS_ENDPOINT, index_name); idx.sync(); return idx
        raise

index = make_index(C.INDEX_NAME, C.CHUNKS_TABLE)
index_fixed = make_index(C.INDEX_FIXED_NAME, C.CHUNKS_FIXED_TABLE)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.3 — Query it three ways

# COMMAND ----------
def show(res):
    cols = [c["name"] for c in res["manifest"]["columns"]]
    for row in res["result"]["data_array"]:
        d = dict(zip(cols, row))
        print(f"{d.get('score', 0):.3f}  {d['doc_id']:<18} {d['text'][:90]!r}")

q = "How much does the Pro plan cost?"
print("— ANN (semantic) —");  show(index.similarity_search(query_text=q, columns=["doc_id", "text"], num_results=3))
print("— HYBRID —");          show(index.similarity_search(query_text=q, columns=["doc_id", "text"], num_results=3, query_type="HYBRID"))
print("— filtered to faq —"); show(index.similarity_search(query_text=q, columns=["doc_id", "text"], num_results=3, filters={"doc_id": "faq"}))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.4 — Where hybrid wins: exact tokens
# MAGIC Pure semantic search can miss rare literal strings (error codes, product names). Compare both modes:

# COMMAND ----------
q2 = "HTTP 413"
print("ANN:");    show(index.similarity_search(query_text=q2, columns=["doc_id", "text"], num_results=2))
print("HYBRID:"); show(index.similarity_search(query_text=q2, columns=["doc_id", "text"], num_results=2, query_type="HYBRID"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.5 — Re-ranking
# MAGIC First-stage retrieval is fast but approximate. A **re-ranker** (cross-encoder) re-scores the top-N more carefully. Trade-off: extra latency. Try the built-in one — if your Free workspace doesn't allow it, the cell tells you.

# COMMAND ----------
try:
    from databricks.ai_search.reranker import DatabricksReranker
    res = index.similarity_search(query_text=q, columns=["doc_id", "text"], num_results=3, query_type="HYBRID",
                                  reranker=DatabricksReranker(columns_to_rerank=["text"]))
    show(res)
except Exception as e:
    print("Reranker not available here:", str(e)[:200])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 3.6 — Keeping the index fresh (CI/CD concept)
# MAGIC Add a chunk to the Delta table, then `index.sync()`. This one call is what your scheduled Job runs in production.

# COMMAND ----------
spark.sql(f"""INSERT INTO {C.CHUNKS_TABLE}
 VALUES ('faq-markdown-99','faq','Test','[Test] Nimbus supports the Mars region for testing.','markdown')""")
index.sync(); time.sleep(60)
show(index.similarity_search(query_text="Mars region", columns=["doc_id", "text"], num_results=1))
spark.sql(f"DELETE FROM {C.CHUNKS_TABLE} WHERE chunk_id='faq-markdown-99'"); index.sync()

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 3
# MAGIC - [ ] Query "Pro plan cost" returns `billing_policy` first
# MAGIC - [ ] Filter query returns only `faq`
# MAGIC - [ ] The Mars chunk appeared after sync, then was deleted
# MAGIC
# MAGIC ### Common errors
# MAGIC | Symptom | Fix |
# MAGIC |---|---|
# MAGIC | "Change data feed not enabled" | Re-run Stage 2.4 ALTER TABLE |
# MAGIC | Endpoint quota error | Free Edition allows one endpoint — delete extras in *Compute → Vector Search* |
# MAGIC | Index stuck `PROVISIONING` | Normal for ~5–15 min; check *Catalog → index → Overview* |
# MAGIC | Empty results right after create | Initial sync not finished — wait or `index.sync()` |
