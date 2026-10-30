"""Thin wrappers so notebooks stay short and survive SDK renames."""
from __future__ import annotations

from typing import Any


def get_vs_client(**kwargs):
    """Vector Search was renamed AI Search (databricks-ai-search). Support both."""
    try:
        from databricks.ai_search.client import VectorSearchClient  # newer package
    except ImportError:  # pragma: no cover
        from databricks.vector_search.client import VectorSearchClient
    return VectorSearchClient(disable_notice=True, **kwargs)


def get_openai_client():
    """OpenAI-compatible client pointed at this workspace's serving endpoints.

    Works on serverless notebooks with no token handling (exam: Foundation Model APIs).
    """
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient().serving_endpoints.get_open_ai_client()


def chat(messages: list[dict], model: str, temperature: float = 0.0,
         max_tokens: int = 512, **kwargs: Any) -> str:
    """Single-turn chat completion; returns the text only."""
    client = get_openai_client()
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature,
        max_tokens=max_tokens, **kwargs,
    )
    return resp.choices[0].message.content


def list_foundation_endpoints(prefix: str = "databricks-") -> list[dict]:
    """Discover which Foundation Model endpoints your workspace actually has."""
    from databricks.sdk import WorkspaceClient

    out = []
    for ep in WorkspaceClient().serving_endpoints.list():
        if ep.name and ep.name.startswith(prefix):
            out.append({"name": ep.name, "task": getattr(ep, "task", None)})
    return sorted(out, key=lambda d: d["name"])


def embed(texts: list[str], model: str) -> list[list[float]]:
    client = get_openai_client()
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]
