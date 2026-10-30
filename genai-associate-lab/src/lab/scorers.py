"""Custom scorers for mlflow.genai.evaluate (Exam §6: custom Scorers, judges needing ground truth).

Built-in judges and whether they need ground truth (`expectations`):
  needs expected_response / expected_facts : Correctness, Equivalence, RetrievalSufficiency
  no ground truth needed                   : Safety, RelevanceToQuery, RetrievalGroundedness,
                                             RetrievalRelevance, Guidelines, Fluency, ...
"""
from __future__ import annotations

import re

from mlflow.entities import Feedback
from mlflow.genai.scorers import scorer


@scorer
def cites_a_source(outputs) -> Feedback:
    """Code-based scorer: answer must cite at least one [doc_id]."""
    text = outputs.get("answer", "") if isinstance(outputs, dict) else str(outputs)
    ok = bool(re.search(r"\[[a-z0-9_]+\]", text))
    return Feedback(value="yes" if ok else "no",
                    rationale="Found a [doc_id] citation" if ok else "No citation in answer")


@scorer
def no_pii_leak(outputs) -> bool:
    from lab.guardrails import mask_pii

    text = outputs.get("answer", "") if isinstance(outputs, dict) else str(outputs)
    return mask_pii(text) == text


@scorer
def retrieved_expected_doc(outputs, expectations) -> Feedback:
    """Ground-truth scorer: did the pipeline surface the doc we expect?"""
    expected = set(expectations.get("expected_docs", []))
    got = set(outputs.get("sources", [])) if isinstance(outputs, dict) else set()
    hit = bool(expected & got)
    return Feedback(value=hit, rationale=f"expected={sorted(expected)} got={sorted(got)}")


@scorer
def concise(outputs) -> Feedback:
    text = outputs.get("answer", "") if isinstance(outputs, dict) else str(outputs)
    n = len(text.split())
    return Feedback(value=n <= 150, rationale=f"{n} words")
