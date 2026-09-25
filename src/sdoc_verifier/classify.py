"""Deterministic classification of shipping-operations email."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from sdoc_verifier.models import Category, Confidence

SUBJECT_CONFIDENCE = 0.95
BODY_CONFIDENCE = 0.85
FALLBACK_CONFIDENCE = 0.55
Tier = Literal["subject", "body"]


@dataclass(frozen=True)
class Rule:
    name: str
    category: Category
    tier: Tier
    patterns: tuple[str, ...]

    def matches(self, text: str) -> str | None:
        normalized = re.sub(r"\s+", " ", text).casefold()
        for pattern in self.patterns:
            if pattern in normalized:
                return pattern
        return None


RULE_SPEC: tuple[tuple[str, Category, Tier, tuple[str, ...]], ...] = (
    (
        "spam",
        "SPAM",
        "subject",
        (
            "claim now",
            "exclusive offer",
            "limited time",
            "you have won",
            "verify your account",
            "bank details",
            "unsubscribe now",
        ),
    ),
    (
        "comparison",
        "BL_COMPARISON",
        "subject",
        ("draft bl", "draft bill of lading", "compare si", "confirm documents"),
    ),
    (
        "si_request",
        "SI_REQUEST",
        "subject",
        ("request si", "shipping instruction needed", "prepare si"),
    ),
    (
        "invoice",
        "INVOICE_QUERY",
        "subject",
        ("invoice", "local charges", "freight invoice", "missing gr"),
    ),
    (
        "general",
        "GENERAL",
        "subject",
        ("operations update", "berthing report", "reminder", "delivery update"),
    ),
    (
        "spam_body",
        "SPAM",
        "body",
        ("click here", "claim your", "bank details", "verify your account"),
    ),
    (
        "comparison_body",
        "BL_COMPARISON",
        "body",
        (
            "compare the si and",
            "check the draft bl",
            "verify the bl",
            "bl against the si",
            "si and draft bl",
            "confirm the documents",
        ),
    ),
    (
        "si_request_body",
        "SI_REQUEST",
        "body",
        ("shipping instruction", "please provide the si", "request si"),
    ),
    (
        "invoice_body",
        "INVOICE_QUERY",
        "body",
        ("query on invoice", "local charge", "missing gr", "freight invoice"),
    ),
    (
        "general_body",
        "GENERAL",
        "body",
        ("operations update", "please follow the previous instruction", "reminder"),
    ),
)

RULES = tuple(Rule(*spec) for spec in RULE_SPEC)
_SUBJECT_RULES = tuple(rule for rule in RULES if rule.tier == "subject")
_BODY_RULES = tuple(rule for rule in RULES if rule.tier == "body")


class EmailLike(Protocol):
    @property
    def subject(self) -> str | None: ...

    @property
    def body(self) -> str: ...


@dataclass(frozen=True)
class Email:
    subject: str | None
    body: str


def _first_match(rules: tuple[Rule, ...], text: str) -> tuple[Rule, str] | None:
    for rule in rules:
        pattern = rule.matches(text)
        if pattern is not None:
            return rule, pattern
    return None


def decide(subject: str | None, body: str) -> tuple[Category, Confidence]:
    """Return a category and confidence using subject, body, then fallback rules."""
    subject_hit = _first_match(_SUBJECT_RULES, subject or "")
    if subject_hit is not None:
        rule, pattern = subject_hit
        return rule.category, Confidence(
            SUBJECT_CONFIDENCE, f"subject rule {rule.name}: {pattern!r}"
        )

    body_hit = _first_match(_BODY_RULES, body or "")
    if body_hit is not None:
        rule, pattern = body_hit
        return rule.category, Confidence(
            BODY_CONFIDENCE, f"body rule {rule.name}: {pattern!r}"
        )

    return "GENERAL", Confidence(FALLBACK_CONFIDENCE, "fallback: no rule matched")


def classify_email(email: EmailLike) -> tuple[Category, Confidence]:
    return decide(email.subject, email.body)


__all__ = [
    "BODY_CONFIDENCE",
    "FALLBACK_CONFIDENCE",
    "RULES",
    "RULE_SPEC",
    "Email",
    "EmailLike",
    "Rule",
    "SUBJECT_CONFIDENCE",
    "classify_email",
    "decide",
]
