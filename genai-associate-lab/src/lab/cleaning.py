"""Parsing + cleaning (Exam §2: choose the right Python package, filter extraneous content)."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Which package for which format -- a classic exam question.
PARSER_FOR_EXTENSION = {
    ".pdf": "pypdf (text PDFs) | unstructured / PyMuPDF / OCR for scanned PDFs",
    ".html": "BeautifulSoup4 (or unstructured) -- drop nav/footer/script",
    ".md": "plain read; split on headers",
    ".docx": "python-docx / unstructured",
    ".pptx": "python-pptx / unstructured",
    ".csv": "pandas / spark.read",
}


def read_pdf(path: str | Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n\n".join((p.extract_text() or "") for p in reader.pages)


def read_html(path: str | Path) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    # keep heading structure as markdown so header-aware chunking still works
    for level in range(1, 5):
        for h in soup.find_all(f"h{level}"):
            h.string = f"\n{'#' * level} {h.get_text(strip=True)}\n"
    return soup.get_text("\n")


def read_any(path: str | Path) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".pdf":
        return read_pdf(p)
    if ext in {".html", ".htm"}:
        return read_html(p)
    return p.read_text(encoding="utf-8")


_BOILERPLATE = [
    r"(?im)^\s*page \d+ of \d+\s*$",
    r"(?im)^\s*confidential\s*[-–]\s*nimbus cloud internal\s*$",
    r"(?im)^\s*(cookie|privacy) (settings|notice).*$",
    r"(?im)^\s*©.*all rights reserved.*$",
    r"(?im)^\s*(share|tweet|subscribe to our newsletter).*$",
]


def strip_boilerplate(text: str) -> str:
    for pat in _BOILERPLATE:
        text = re.sub(pat, "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", text.lower()).encode()).hexdigest()[:16]


def dedupe(chunks: list[dict]) -> list[dict]:
    """Exact-duplicate removal on normalised text (near-dup: MinHash, out of scope)."""
    seen, out = set(), []
    for c in chunks:
        h = content_hash(c["text"])
        if h not in seen:
            seen.add(h)
            out.append(c)
    return out


def is_low_quality(chunk_text: str, min_chars: int = 60) -> bool:
    """Filter chunks that hurt retrieval: too short, or mostly non-alphabetic."""
    t = chunk_text.strip()
    if len(t) < min_chars:
        return True
    alpha = sum(ch.isalpha() for ch in t)
    return alpha / max(len(t), 1) < 0.5
