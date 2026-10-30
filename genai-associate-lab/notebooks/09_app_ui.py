# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 9 — Put a UI on it (Databricks Apps)
# MAGIC **Goal:** deploy `apps/chat_app` — a Streamlit chat front end that calls your serving endpoint.
# MAGIC
# MAGIC **Exam link:** §4 develop a user-facing interface for an agent (Apps, Slack, Teams) · control access to resources.
# MAGIC
# MAGIC **Free Edition:** up to 3 apps; each auto-stops after ~24 h (just restart it).
# MAGIC
# MAGIC ## Steps (UI, not code)
# MAGIC 1. **Compute → Apps → Create app → Custom** (Streamlit). Name: `nimbus-support-chat`.
# MAGIC 2. In *Configure → App resources* add a **Serving endpoint** resource, key `serving-endpoint`, your agent endpoint, permission *Can query*. *(This is least-privilege: the app's service principal gets only this.)*
# MAGIC 3. Workspace → open `apps/chat_app` → copy `app.py`, `app.yaml`, `requirements.txt` into the app's source folder (or *Deploy → choose the Git folder path*).
# MAGIC 4. **Deploy**. Open the URL.
# MAGIC
# MAGIC ### Why a resource instead of a token?
# MAGIC Apps run as a **service principal**. Declaring the endpoint as a resource grants that principal access and injects the endpoint name as an env var — no secrets in code. Same idea as Stage 5 *resources* for models.

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 9.1 — Test the app logic from a notebook first

# COMMAND ----------
import os, sys
sys.path.append(os.path.abspath("../apps/chat_app"))
os.environ.setdefault("SERVING_ENDPOINT", "agents_workspace-genai_lab-nimbus_support_agent")
from backend import ask
print(ask([{"role": "user", "content": "What roles exist in a workspace?"}]))

# COMMAND ----------
# MAGIC %md
# MAGIC ## ✅ Checkpoint 9
# MAGIC - [ ] The app URL loads and answers "What roles exist?" with Owner/Admin/Member
# MAGIC - [ ] You can explain app-vs-user authorization: the app calls the endpoint **as its service principal** (app auth); per-user (OBO) auth exists for row-level access needs.
# MAGIC
# MAGIC ## 🎉 You've built it end to end
# MAGIC data → chunks → index → measured retrieval → RAG model → agent → evaluation → serving → UI.
# MAGIC Next: `docs/extensions.md` (Genie, MCP, Lakebase memory, Agent Bricks, CI/CD).
