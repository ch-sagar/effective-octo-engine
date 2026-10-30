# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 2 — Turn raw files into clean chunks in a Delta table
# MAGIC **Goal:** parse PDF/HTML/MD → clean → check licences → chunk → write `doc_chunks` (Change Data Feed ON).
# MAGIC
# MAGIC **Why:** retrieval quality is capped by chunk quality. Garbage in, garbage retrieved.
# MAGIC
# MAGIC **Exam link:** §2 chunking strategy, filter extraneous content, choose Python package, write chunks to Delta in UC, source quality · §5 licensing.

# COMMAND ----------
# MAGIC %pip install -q pypdf beautifulsoup4
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, glob, pandas as pd
sys.path.append(os.path.abspath("../src"))
from lab import config as C, cleaning, chunking

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 2.1 — Governance first: which documents are *allowed*?
# MAGIC Two files must never reach a customer-facing bot: one has staff PII, one is a third party's copyrighted benchmark. Decide **before** embedding — once text is in an index it's hard to purge.

# COMMAND ----------
lic = spark.table(C.LICENSE_TABLE).toPandas()
display(lic)
approved = set(lic.loc[lic.approved_for_rag == "yes", "doc_id"])
print("approved:", sorted(approved))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 2.2 — Parse (right tool per format) and clean
# MAGIC Look at `PARSER_FOR_EXTENSION` — this mapping is the exam question. Then compare raw vs cleaned for the HTML page: nav, footer, cookie text must disappear.

# COMMAND ----------
print(cleaning.PARSER_FOR_EXTENSION)
docs = {}
for path in sorted(glob.glob(f"{C.VOLUME_PATH}/*")):
    doc_id = os.path.splitext(os.path.basename(path))[0]
    if doc_id not in approved:
        print("SKIP (not approved):", doc_id); continue
    docs[doc_id] = cleaning.strip_boilerplate(cleaning.read_any(path))
print(docs["api_rate_limits"][:400])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 2.3 — Compare chunking strategies on the *same* text
# MAGIC Predict first: which strategy keeps "Free plan: 5 requests per second…" together with its heading?

# COMMAND ----------
sample = docs["api_rate_limits"]
for name, fn in chunking.STRATEGIES.items():
    ch = fn(sample)
    print(f"--- {name}: {len(ch)} chunks, avg {sum(len(c['text']) for c in ch)//len(ch)} chars")
    print(ch[0]["text"][:200].replace("\n", " ⏎ "))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 2.4 — Build two chunk tables (we'll *measure* which wins in Stage 4)
# MAGIC `delta.enableChangeDataFeed = true` is **required** for a Delta Sync vector index.

# COMMAND ----------
def build(strategy: str) -> pd.DataFrame:
    rows = []
    for doc_id, text in docs.items():
        for c in chunking.dedupe(chunking.STRATEGIES[strategy](text)):
            if cleaning.is_low_quality(c["text"]):
                continue
            rows.append({"chunk_id": f"{doc_id}-{strategy}-{c['chunk_index']}", "doc_id": doc_id,
                         "section": c["section"], "text": c["text"], "strategy": strategy})
    return pd.DataFrame(rows)

for strategy, table in [("markdown", C.CHUNKS_TABLE), ("fixed", C.CHUNKS_FIXED_TABLE)]:
    df = build(strategy)
    spark.createDataFrame(df).write.mode("overwrite").option("delta.enableChangeDataFeed", "true").saveAsTable(table)
    spark.sql(f"ALTER TABLE {table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
    print(table, len(df), "chunks")

display(spark.table(C.CHUNKS_TABLE).limit(10))

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 2
# MAGIC - [ ] Two SKIP lines printed (incident postmortem, latency benchmark)
# MAGIC - [ ] HTML output has **no** "Subscribe", "Cookie", "©"
# MAGIC - [ ] `doc_chunks` has roughly 20–30 rows; `SHOW TBLPROPERTIES workspace.genai_lab.doc_chunks` shows `delta.enableChangeDataFeed = true`
# MAGIC
# MAGIC ### Try it
# MAGIC Change `max_chars` in `by_markdown_header` to 300, rebuild, and see what happens to chunk count. Too small = lost context; too big = diluted embeddings and wasted prompt tokens. The embedding model's context length is the hard upper limit.
