# Lab guide — how to work through this like training, not reading

## Ground rules
1. **Predict, then run.** Before each marked cell, write down what you expect. Wrong predictions are where learning happens.
2. **Break one thing on purpose per stage.** Remove the few-shot example, shrink chunks, drop `resources` when logging. Seeing the failure teaches more than the success.
3. **Never skip a checkpoint.** Later stages assume earlier tables/indexes exist.
4. **Keep a `notes.md`** with one line per stage: *what surprised me*.
5. **Stop for the day at a stage boundary** and delete expensive things (endpoints, apps).

## The mental model (draw it from memory after Stage 6)
- **Offline path** (batch, runs on a schedule): files → parse → clean → chunk → Delta → index sync.
- **Online path** (per request): question → guardrails → retrieve → prompt → LLM → (tools loop) → guardrails → answer.
- **Feedback path**: traces + evaluation → change chunking / prompt / model → re-evaluate.

When something is wrong, ask *which path* it lives in. That single question solves most debugging.

## Stage-by-stage coaching

| Stage | What to notice | If you get stuck |
|---|---|---|
| 0 | Three-level names `catalog.schema.object`; Volumes vs tables | `SHOW CATALOGS`, `SHOW SCHEMAS IN workspace` |
| 1 | Format control comes from examples + structure, not pleading | Print raw `out` before `json.loads` |
| 2 | Governance happens *before* embedding | Compare `docs` keys vs Volume listing |
| 3 | Hybrid beats semantic on literal tokens like `HTTP 413` | Check index status in Catalog UI |
| 4 | Averages hide failures; read the misses | Print retrieved chunk text, not only doc ids |
| 5 | `resources` = least-privilege auth for serving | Read the 403 body; it names the missing resource |
| 6 | The trace tree *is* the agent's reasoning | Lower `range(5)` to 2 to see forced early exit |
| 7 | Separate retrieval failures from generation failures | Open one failing trace per metric |
| 8 | Cold starts, scale-to-zero, quotas | Serving → endpoint → *Events* tab |
| 9 | App service principal ≠ you | App → *Logs* tab |

## Final exercises (this is where you prove you can build, not follow)
1. **New domain.** Replace the corpus with 5 documents from something you know (e.g., your KPMG data-platform runbooks, sanitized). Re-run Stages 2–7 and report MRR before/after.
2. **Add a third tool**: `get_incident_status(region)` returning canned JSON. Update the schema, test it alone, extend the evaluation set with 3 questions that need it.
3. **Memory**: store the last 5 turns per `session_id` in a Delta table (or Lakebase — see extensions) and inject them into the prompt.
4. **Regression gate**: write a script that runs `mlflow.genai.evaluate` and exits non-zero if `correctness` mean < 0.8. Wire it to GitHub Actions.
5. **Break-it day**: write 10 adversarial prompts (injection, PII, off-topic, ambiguous). Measure how many get through. Fix with guardrails, re-measure.

## How the six exam sections map to your build
| Exam section | Where you practised it |
|---|---|
| 1 Design Applications | Stage 1 (prompt/format, model selection), Stage 6 (tool design & order), extensions (Agent Bricks) |
| 2 Data Preparation | Stages 2–4 |
| 3 Application Development | Stages 1, 5, 6 (guardrails, augmentation, MLflow/Agent Framework) |
| 4 Assembling & Deploying | Stages 3, 5, 6, 8, 9 |
| 5 Governance | Stage 2 (licence gate), Stage 5 (masking, guardrails) |
| 6 Evaluation & Monitoring | Stages 4, 7, 8 |

Full objective-by-objective table: `docs/exam-map.md`.
