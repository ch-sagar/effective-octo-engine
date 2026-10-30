"""Chunking strategies (Exam §2: chunking for document structure + model constraints).

Every function returns a list of dicts: {"text", "chunk_index", "section"}.
Token counts are approximated (~4 chars/token) so the module has no heavy deps;
swap `approx_tokens` for tiktoken / the model tokenizer when precision matters.
"""
from __future__ import annotations

import re


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def fixed_size(text: str, chunk_chars: int = 800, overlap_chars: int = 100) -> list[dict]:
    """Naive fixed-width windows. Fast, ignores structure, can cut mid-sentence."""
    if overlap_chars >= chunk_chars:
        raise ValueError("overlap must be smaller than chunk size")
    step = chunk_chars - overlap_chars
    chunks = []
    for i, start in enumerate(range(0, max(len(text), 1), step)):
        piece = text[start:start + chunk_chars].strip()
        if piece:
            chunks.append({"text": piece, "chunk_index": i, "section": ""})
        if start + chunk_chars >= len(text):
            break
    return chunks


_SEPARATORS = ["\n\n", "\n", ". ", " "]


def recursive(text: str, chunk_chars: int = 800, overlap_chars: int = 100) -> list[dict]:
    """Split on the largest separator that keeps pieces under the limit
    (same idea as LangChain's RecursiveCharacterTextSplitter)."""

    def split(t: str, seps: list[str]) -> list[str]:
        if len(t) <= chunk_chars or not seps:
            return [t]
        sep, rest = seps[0], seps[1:]
        parts = t.split(sep)
        if len(parts) == 1:
            return split(t, rest)
        merged, cur = [], ""
        for p in parts:
            candidate = f"{cur}{sep}{p}" if cur else p
            if len(candidate) <= chunk_chars:
                cur = candidate
            else:
                if cur:
                    merged.append(cur)
                if len(p) > chunk_chars:
                    merged.extend(split(p, rest))
                    cur = ""
                else:
                    cur = p
        if cur:
            merged.append(cur)
        return merged

    pieces = [p.strip() for p in split(text, _SEPARATORS) if p.strip()]
    out = []
    for i, p in enumerate(pieces):
        if i > 0 and overlap_chars:
            p = pieces[i - 1][-overlap_chars:] + " " + p
        out.append({"text": p, "chunk_index": i, "section": ""})
    return out


_HEADING = re.compile(r"^(#{1,4})\s+(.*)$", re.MULTILINE)


def by_markdown_header(text: str, max_chars: int = 1200) -> list[dict]:
    """Structure-aware: one chunk per heading section; oversized sections are
    re-split recursively. The heading path is prepended so the chunk is
    self-describing ("contextual chunk headers" improve retrieval)."""
    matches = list(_HEADING.finditer(text))
    if not matches:
        return recursive(text, max_chars, 100)
    sections, path = [], []
    for i, m in enumerate(matches):
        level, title = len(m.group(1)), m.group(2).strip()
        path = path[: level - 1] + [title]
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        if body:
            sections.append((" > ".join(path), body))
    out = []
    for sec, body in sections:
        header = f"[{sec}]\n"
        if len(body) + len(header) <= max_chars:
            out.append({"text": header + body, "chunk_index": len(out), "section": sec})
        else:
            for sub in recursive(body, max_chars - len(header), 100):
                out.append({"text": header + sub["text"], "chunk_index": len(out), "section": sec})
    return out


def sentence_window(text: str, window: int = 3) -> list[dict]:
    """Index single sentences but store the surrounding window as `context`
    (small-to-big retrieval: match precisely, answer with more context)."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    out = []
    for i, s in enumerate(sentences):
        lo, hi = max(0, i - window), min(len(sentences), i + window + 1)
        out.append({"text": s, "chunk_index": i, "section": "",
                    "context": " ".join(sentences[lo:hi])})
    return out


STRATEGIES = {
    "fixed": fixed_size,
    "recursive": recursive,
    "markdown": by_markdown_header,
}
