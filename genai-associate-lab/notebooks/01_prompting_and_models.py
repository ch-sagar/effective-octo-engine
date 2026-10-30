# Databricks notebook source
# MAGIC %md
# MAGIC # Stage 1 — Talk to an LLM properly
# MAGIC **Goal:** control output format, compare two models, and understand why we later *ground* the model with retrieval.
# MAGIC
# MAGIC **Exam link:** §1 design a prompt for a specific format · select model for a task · §3 prompt augmentation, select best LLM from metrics.

# COMMAND ----------
# MAGIC %pip install -q databricks-sdk mlflow>=3
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os, sys, json, time
sys.path.append(os.path.abspath("../src"))
from lab import config as C
from lab.compat import chat

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 1.1 — A prompt has parts
# MAGIC **system** = persona + rules. **user** = the task. Few-shot **examples** teach format better than adjectives.
# MAGIC Run it, then *change one thing at a time* (remove the example; remove "ONLY JSON") and watch what breaks.

# COMMAND ----------
SYSTEM = "You are a support-ticket classifier. Reply with ONLY a JSON object, no prose."
FEW_SHOT = [
    {"role": "user", "content": "My invoice shows the wrong amount."},
    {"role": "assistant", "content": '{"category": "billing", "urgency": "medium"}'},
    {"role": "user", "content": "API returns 503 for every call, we're down!"},
    {"role": "assistant", "content": '{"category": "outage", "urgency": "high"}'},
]
ticket = "How do I add a teammate to our workspace?"
out = chat([{"role": "system", "content": SYSTEM}, *FEW_SHOT, {"role": "user", "content": ticket}],
           model=C.LLM_ENDPOINT)
print(out)
print(json.loads(out))   # raises if the model ignored the format → that's your signal

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 1.2 — Structured output (more reliable than begging)
# MAGIC `response_format` with a JSON schema makes the *server* enforce structure. Not every endpoint supports it — if you get an error, keep the few-shot approach.

# COMMAND ----------
schema = {"type": "json_schema", "json_schema": {"name": "ticket", "strict": True, "schema": {
    "type": "object",
    "properties": {"category": {"type": "string", "enum": ["billing", "outage", "how_to", "security"]},
                   "urgency": {"type": "string", "enum": ["low", "medium", "high"]}},
    "required": ["category", "urgency"], "additionalProperties": False}}}
try:
    print(chat([{"role": "user", "content": ticket}], model=C.LLM_ENDPOINT, response_format=schema))
except Exception as e:
    print("Structured output not supported on this endpoint:", str(e)[:200])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 1.3 — Why we need RAG: ask about our fictional company
# MAGIC The model has never seen Nimbus Cloud. Watch it guess.

# COMMAND ----------
q = "How much does the Nimbus Cloud Pro plan cost?"
print(chat([{"role": "user", "content": q}], model=C.LLM_ENDPOINT))

# COMMAND ----------
# MAGIC %md
# MAGIC Now **augment** the prompt with the fact yourself (this is all RAG is, automated):

# COMMAND ----------
ctx = "The Pro plan costs $49 per month and includes 500,000 requests."
print(chat([{"role": "system", "content": "Answer ONLY from the context. If missing, say you don't know."},
            {"role": "user", "content": f"Context: {ctx}\n\nQuestion: {q}"}], model=C.LLM_ENDPOINT))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Step 1.4 — Pick a model with evidence, not vibes
# MAGIC Run the same 3 questions on two models; log latency and a crude correctness check to MLflow. (Stage 7 replaces the crude check with LLM judges.)

# COMMAND ----------
import mlflow
mlflow.set_experiment(C.EXPERIMENT_PATH)
tests = [("What is 17*23? Number only.", "391"), ("Capital of Australia? One word.", "Canberra"),
         ("Spell 'lollipop' backwards. Only the word.", "popillol")]
for model in [C.LLM_ENDPOINT, C.LLM_ENDPOINT_ALT]:
    with mlflow.start_run(run_name=f"compare-{model}"):
        t0, ok = time.time(), 0
        for p, want in tests:
            try:
                ok += want.lower() in chat([{"role": "user", "content": p}], model=model, max_tokens=60).lower()
            except Exception as e:
                print(model, "failed:", str(e)[:120])
        mlflow.log_params({"model": model})
        mlflow.log_metrics({"accuracy": ok / len(tests), "avg_latency_s": (time.time() - t0) / len(tests)})
        print(model, ok, "/", len(tests))

# COMMAND ----------
# MAGIC %md
# MAGIC Open **Experiments** in the left sidebar → `genai_associate_lab` → select both runs → *Compare*.
# MAGIC
# MAGIC ## ✅ Checkpoint 1
# MAGIC - [ ] Step 1.1 printed a parsed dict
# MAGIC - [ ] Step 1.3 first answer was a guess / "I don't know"; second was `$49`
# MAGIC - [ ] Two runs visible in MLflow with `accuracy` and `avg_latency_s`
# MAGIC
# MAGIC ### Think about it (exam-style)
# MAGIC 1. Why is `temperature=0` the default in this lab? *(deterministic, easier to evaluate)*
# MAGIC 2. A 70B and a 20B model tie on accuracy. Which do you ship and why? *(cost/latency)*
# MAGIC 3. When would few-shot beat a longer system prompt? *(format fidelity)*
