"""Guardrails + masking (Exam §3 guardrails, §5 Governance).

Layered defence -- cheap deterministic checks first, LLM-based checks second:
  input  : length cap -> prompt-injection patterns -> PII masking -> topic deny-list
  output : PII masking -> safety / groundedness judges (see notebook 11)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)\d{3}[\s-]?\d{3,4}(?!\d)"),
    "CARD": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "IPV4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (the |your )?(system|previous) (prompt|instructions)",
    r"you are now (dan|in developer mode|unrestricted)",
    r"reveal (your |the )?(system|hidden) prompt",
    r"print (your |the )?(instructions|system prompt)",
    r"act as .* without (any )?(restrictions|filters)",
]
_INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

DENY_TOPICS = ["medical advice", "legal advice", "stock tips", "build a weapon"]


def mask_pii(text: str, replacement: str = "[{label}]") -> str:
    # CARD before PHONE so long digit runs are labelled correctly
    for label in ("EMAIL", "CARD", "IPV4", "PHONE"):
        text = PII_PATTERNS[label].sub(replacement.format(label=label), text)
    return text


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(text))


@dataclass
class GuardResult:
    allowed: bool
    text: str
    reasons: list[str] = field(default_factory=list)


def check_input(user_text: str, max_chars: int = 2000) -> GuardResult:
    reasons: list[str] = []
    if len(user_text) > max_chars:
        return GuardResult(False, "", ["input_too_long"])
    if looks_like_injection(user_text):
        return GuardResult(False, "", ["prompt_injection"])
    lowered = user_text.lower()
    if any(t in lowered for t in DENY_TOPICS):
        return GuardResult(False, "", ["denied_topic"])
    masked = mask_pii(user_text)
    if masked != user_text:
        reasons.append("pii_masked")
    return GuardResult(True, masked, reasons)


def check_output(model_text: str) -> GuardResult:
    masked = mask_pii(model_text)
    reasons = ["pii_masked"] if masked != model_text else []
    return GuardResult(True, masked, reasons)


REFUSAL = ("I can't help with that request. I can answer questions about "
           "Nimbus Cloud billing, limits, security and onboarding.")
