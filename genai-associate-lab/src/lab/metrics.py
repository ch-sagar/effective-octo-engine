"""Retrieval metrics (Exam §2 'use tools and metrics to evaluate retrieval').

`retrieved` = ranked list of doc ids returned by the retriever.
`relevant`  = set of doc ids that should have been returned (ground truth).
"""
from __future__ import annotations

from statistics import mean


def hit_rate_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    return float(any(d in relevant for d in retrieved[:k]))


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    top = retrieved[:k]
    return (sum(d in relevant for d in top) / len(top)) if top else 0.0


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for i, d in enumerate(retrieved, start=1):
        if d in relevant:
            return 1.0 / i
    return 0.0


def evaluate_retriever(rows: list[dict], k: int = 5) -> dict:
    """rows: [{"retrieved": [...], "relevant": [...]}, ...] -> aggregate metrics."""
    rel = [set(r["relevant"]) for r in rows]
    ret = [r["retrieved"] for r in rows]
    return {
        f"hit_rate@{k}": mean(hit_rate_at_k(a, b, k) for a, b in zip(ret, rel)),
        f"recall@{k}": mean(recall_at_k(a, b, k) for a, b in zip(ret, rel)),
        f"precision@{k}": mean(precision_at_k(a, b, k) for a, b in zip(ret, rel)),
        "mrr": mean(reciprocal_rank(a, b) for a, b in zip(ret, rel)),
        "n": len(rows),
    }
