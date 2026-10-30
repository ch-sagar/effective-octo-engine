# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 8 — Deploy the agent and watch it run
# MAGIC **Goal:** serve the registered agent as a REST endpoint, query it, inspect traces, and try batch inference with `ai_query()`.
# MAGIC
# MAGIC **Exam link:** §4 serve an app using Foundation Model APIs · `ai_query()` for batch · access control from endpoints · §6 inference logging, AI Gateway (usage, rate limits), cost control.
# MAGIC
# MAGIC **Free Edition reality check:** limited number of endpoints, **no GPU / no provisioned throughput**. Our agent is a CPU model that calls pay-per-token Foundation Model APIs, which fits. If `agents.deploy` is refused, jump to the *Fallback* cell — you still learn the same concepts.

# COMMAND ----------
# MAGIC %pip install -q databricks-agents mlflow>=3 databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, mlflow, time
sys.path.append(os.path.abspath("../src"))
from lab import config as C
mlflow.set_registry_uri("databricks-uc")
latest = max(int(v.version) for v in mlflow.MlflowClient().search_model_versions(f"name='{C.AGENT_MODEL_NAME}'"))
print("deploying", C.AGENT_MODEL_NAME, "v", latest)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 8.1 — Deploy
# MAGIC `agents.deploy` does a lot in one call: creates a Model Serving endpoint, wires the declared *resources* with scoped credentials, enables tracing + a review app, and sets up inference logging. ~10–15 minutes.

# COMMAND ----------
from databricks import agents
try:
    deployment = agents.deploy(C.AGENT_MODEL_NAME, latest, scale_to_zero=True)
    print("endpoint:", deployment.endpoint_name); print("review app:", getattr(deployment, "review_app_url", None))
except Exception as e:
    deployment = None
    print("agents.deploy failed:", str(e)[:500])

# COMMAND ----------
# MAGIC %md
# MAGIC ### Fallback (if the cell above is refused)
# MAGIC Create the endpoint manually: **Serving → Create serving endpoint → Unity Catalog model → `nimbus_support_agent` version → Compute: CPU, Small, scale to zero ON**. Then continue with 8.2 using the name you chose.

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 8.2 — Query the endpoint
# MAGIC Wait for state `READY` (*Serving* page). The first call after scale-to-zero is slow ("cold start") — expected.

# COMMAND ----------
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
ENDPOINT = deployment.endpoint_name if deployment else "agents_workspace-genai_lab-nimbus_support_agent"
client = w.serving_endpoints.get_open_ai_client()
resp = client.responses.create(model=ENDPOINT, input=[{"role": "user", "content": "Does the Free plan have an SLA?"}])
print(resp.output_text if hasattr(resp, "output_text") else resp)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 8.3 — Generate a little traffic, then inspect it
# MAGIC Send 5 varied questions (include one off-topic and one expensive multi-tool). Then open *Serving → your endpoint → Logs / Traces*. Look at: latency distribution, errors, token counts, tool-call counts.

# COMMAND ----------
for q in ["What's the max body size on Pro?", "Cost for 1.2M requests on Enterprise?", "Tell me a joke",
          "Where is my data stored?", "How do I rotate my API key?"]:
    try:
        r = client.responses.create(model=ENDPOINT, input=[{"role": "user", "content": q}])
        print("Q:", q, "\nA:", (getattr(r, "output_text", "") or str(r))[:160], "\n")
    except Exception as e:
        print("ERR", q, str(e)[:120])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 8.4 — Monitoring & cost levers (know these for interviews and the exam)
# MAGIC | Need | Databricks feature |
# MAGIC |---|---|
# MAGIC | See every request/response | **Inference tables** (payload logging to Delta) via AI Gateway |
# MAGIC | Who used how many tokens | **Usage tracking** system tables (`system.serving.*`) *(may be unavailable on Free)* |
# MAGIC | Stop runaway spend | **Rate limits** per user/endpoint in AI Gateway; cap loops (`range(5)`) |
# MAGIC | Block bad content | AI Gateway **guardrails** (safety, PII) on input/output |
# MAGIC | Quality over time | **Agent Monitoring** — scheduled judges on a sample of production traces |
# MAGIC | Cut cost | Smaller model, shorter context (`num_results`), caching, batch via `ai_query` |
# MAGIC
# MAGIC Try it in the UI: *Serving → endpoint → Edit AI Gateway* and add a rate limit of 5 queries/minute. Then fire the 5-question loop twice quickly and watch the 429.
# MAGIC
# MAGIC ## Step 8.5 — Batch inference with `ai_query()`
# MAGIC For 10,000 tickets you don't loop over REST — you run SQL in parallel on the data.

# COMMAND ----------
spark.sql(f"""
SELECT question,
       ai_query('{C.LLM_ENDPOINT}',
                CONCAT('Classify into billing/outage/how_to/security. Reply with one word. Ticket: ', question)) AS category
FROM {C.EVAL_TABLE}
LIMIT 8
""").display()

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 8
# MAGIC - [ ] Endpoint `READY`; you got an answer over REST
# MAGIC - [ ] You found a trace for your own request
# MAGIC - [ ] `ai_query` produced a category column
# MAGIC - [ ] You can state when to use `ai_query` (batch, offline, tabular) vs a serving endpoint (interactive, per-request)
# MAGIC
# MAGIC ### 🧹 Clean-up (Free Edition quotas!)
# MAGIC Delete the endpoint when you're done for the day: *Serving → ⋮ → Delete*. Exceeding quota pauses compute for the rest of the day.
