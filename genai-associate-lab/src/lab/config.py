"""Single place for every name used across notebooks.

Free Edition gives you one workspace + one metastore, so we use the default
`workspace` catalog and create our own schema inside it.
Override any value with an environment variable (useful for CI / multi-env promotion).
"""
import os

CATALOG = os.getenv("LAB_CATALOG", "workspace")
SCHEMA = os.getenv("LAB_SCHEMA", "genai_lab")
VOLUME = os.getenv("LAB_VOLUME", "raw_docs")

# Foundation Model API (pay-per-token) endpoints. Names change over time:
# run `lab.compat.list_foundation_endpoints()` and override with env vars if needed.
LLM_ENDPOINT = os.getenv("LAB_LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")
LLM_ENDPOINT_ALT = os.getenv("LAB_LLM_ENDPOINT_ALT", "databricks-gpt-oss-20b")
EMBEDDING_ENDPOINT = os.getenv("LAB_EMBEDDING_ENDPOINT", "databricks-gte-large-en")

# Vector Search (renamed "AI Search" in the SDK; exam still says Vector Search).
# Free Edition: ONE endpoint, ONE search unit, Delta Sync indexes only.
VS_ENDPOINT = os.getenv("LAB_VS_ENDPOINT", "genai_lab_vs")


def fq(name: str) -> str:
    """Fully-qualified three-level UC name: catalog.schema.name"""
    return f"{CATALOG}.{SCHEMA}.{name}"


VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

# Tables
CHUNKS_TABLE = fq("doc_chunks")            # chunks for the main index
CHUNKS_FIXED_TABLE = fq("doc_chunks_fixed")  # alternative strategy for comparison
EVAL_TABLE = fq("golden_eval")
LICENSE_TABLE = fq("source_licenses")
INDEX_NAME = fq("doc_chunks_index")
INDEX_FIXED_NAME = fq("doc_chunks_fixed_index")

# Models / prompts
MODEL_NAME = fq("nimbus_support_rag")
AGENT_MODEL_NAME = fq("nimbus_support_agent")
PROMPT_NAME = fq("support_answer_prompt")

# MLflow experiment (must be an absolute workspace path on Databricks)
EXPERIMENT_PATH = os.getenv("LAB_EXPERIMENT", "/Shared/genai_associate_lab")
