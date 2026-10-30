# Extensions — after the core build works

Do these only after Stage 9. Each is independent. Items marked ⚠️ depend on features Free Edition limits; check the [limitations page](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations) first.

## A. Genie space as a tool (structured data)
1. Create a small table `workspace.genai_lab.usage_by_customer` (customer, plan, month, requests).
2. *Genie → New* → add the table → ask "Which customers exceeded their plan last month?".
3. Use `databricks_langchain.GenieAgent` or the Genie Conversation API as a third tool in `agent.py`; add `DatabricksGenieSpace(genie_space_id=…)` to `resources` when logging.
Why: documents → vector search; numbers → Genie/SQL. A multi-agent supervisor routes between them.

## B. MCP servers (exam §4)
- **Managed** MCP: Databricks hosts servers for Vector Search indexes, UC functions and Genie — you connect with a URL and workspace auth.
- **External**: third-party servers via UC *Connections* (governed credentials).
- **Custom**: your own MCP server hosted as a Databricks App.
Exercise: expose `calculate_overage` as a UC Python function (`CREATE FUNCTION … LANGUAGE PYTHON`) and call it through the managed UC-functions MCP endpoint instead of local Python. ⚠️ needs a SQL warehouse (Free has one 2X-Small).

## C. Persistent memory with Lakebase ⚠️
Free Edition allows one Lakebase project (scale-to-zero). Create a Postgres table `chat_memory(session_id, ts, role, content)`; read last N rows into the prompt; write each turn. Compare with a Delta table: Postgres = low-latency row reads/writes; Delta = analytics.

## D. Agent Bricks (exam §1)
| Brick | Use when | Free? |
|---|---|---|
| Knowledge Assistant | Q&A over documents with citations, no code | ❌ unsupported on Free |
| Information Extraction | Turn unstructured text into structured columns | try it |
| Multi-Agent Supervisor | Route among Genie spaces/agents/tools | try it |
Exam heuristic: *no-code managed + docs Q&A → Knowledge Assistant; custom logic → Agent Framework (what you built).*

## E. LangGraph version of the agent
Rebuild `agent.py` with `langgraph.prebuilt.create_react_agent`, `ChatDatabricks`, and `VectorSearchRetrieverTool`. Compare: lines of code, trace shape, how you cap iterations (`recursion_limit`).

## F. CI/CD
- `tests/` runs on every push (`.github/workflows/ci.yml`).
- `databricks.yml` is a Databricks Asset Bundle: one job that re-runs ingestion and `index.sync()`. `databricks bundle deploy -t dev`.
- Promotion = move the UC alias (`champion`) / prompt alias (`production`) after the evaluation gate passes.

## G. Governance deep-dive
- Row/column masks on `doc_chunks` so only some groups can retrieve certain sections.
- AI Gateway guardrails (safety, PII) on the endpoint ⚠️.
- Document-level ACLs: add `allowed_group` metadata and pass it as a `filters=` value per user.
