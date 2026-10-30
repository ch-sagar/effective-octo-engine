"""Calls the agent's serving endpoint. Separate from the UI so it can be tested from a notebook."""
import os


def _client():
    from databricks.sdk import WorkspaceClient

    # Inside Databricks Apps the SDK authenticates as the app's service principal automatically.
    return WorkspaceClient().serving_endpoints.get_open_ai_client()


def ask(messages: list[dict]) -> str:
    endpoint = os.environ["SERVING_ENDPOINT"]
    resp = _client().responses.create(model=endpoint, input=messages)
    text = getattr(resp, "output_text", None)
    if text:
        return text
    # fall back: last message item
    for item in reversed(resp.output):
        if getattr(item, "type", "") == "message":
            return "".join(c.text for c in item.content if hasattr(c, "text"))
    return "(no answer)"
