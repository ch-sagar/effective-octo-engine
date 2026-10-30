# Databricks Free Edition — what to expect
Source: [docs](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations) (checked 2026-10-30; re-check, this changes).

| Area | Limit | Effect on the lab |
|---|---|---|
| Compute | Serverless only, limited size/usage | Use serverless notebooks; keep jobs small |
| Quotas | Exceed → compute paused for the day (rarely month) | Stop endpoints/apps when done |
| Vector Search | 1 endpoint, 1 search unit, **no Direct Vector Access** | Delta Sync indexes only; both indexes share one endpoint |
| Model Serving | Few active endpoints, **no GPU, no provisioned throughput**, some models unavailable | Our agent is CPU + pay-per-token models |
| Apps | 3 apps, auto-stop after ~24 h | Restart when needed |
| Agent Bricks | Knowledge Assistant unsupported | Extensions §D is conceptual |
| Lakebase | 1 project, scale-to-zero | Extensions §C works |
| SQL | 1 warehouse, 2X-Small | `ai_query` works; keep queries small |
| Network | Outbound limited to trusted domains | Corpus is bundled; no scraping |
| Languages | No R/Scala | n/a |
| Use | Non-commercial only | Learning projects only |

Unverified on Free (may or may not work; the notebooks wrap these in `try/except`): `agents.deploy`, AI Gateway inference tables, system tables, labeling sessions, built-in reranker.
