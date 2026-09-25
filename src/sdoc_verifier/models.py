"""Typed contracts for deterministic shipping-document verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Category = Literal["BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"]
DocFormat = Literal["txt", "xlsx", "docx", "pdf", "unknown"]
DocKind = Literal["SI", "BL", "OTHER", "UNREADABLE"]
Status = Literal["OK", "MISMATCH", "NEEDS_REVIEW"]
ReviewReason = Literal[
    "wrong_doc_type", "missing_attachment", "unreadable", "missing_value"
]
DecisionMaker = Literal["deterministic", "gemini"]

FIELDS: tuple[str, ...] = (
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
)


@dataclass(frozen=True)
class Confidence:
    """Confidence and short evidence for one deterministic stage."""

    score: float
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be within [0.0, 1.0], got {self.score}")


@dataclass(frozen=True)
class ParsedDocument:
    """Normalized parser output for one attachment."""

    path: str
    fmt: DocFormat = "unknown"
    kind: DocKind = "OTHER"
    text: str = ""
    rows: tuple[str, ...] = ()
    scanned: bool = False
    translated: bool = False
    error: str | None = None


@dataclass(frozen=True)
class ExtractedFields:
    """The seven canonical shipment fields extracted from one document."""

    shipper: str = ""
    consignee: str = ""
    notify_party: str = ""
    port_of_loading: str = ""
    port_of_discharge: str = ""
    container_count: str = ""
    gross_weight_kg: str = ""

    def as_dict(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in FIELDS}

    def missing(self) -> list[str]:
        return [name for name in FIELDS if not getattr(self, name).strip()]


@dataclass(frozen=True)
class ComparisonResult:
    """Per-field comparison between a shipping instruction and draft BL."""

    field_matches: dict[str, bool]
    values: dict[str, tuple[str, str]]

    def mismatch_fields(self) -> list[str]:
        return [name for name in FIELDS if self.field_matches.get(name) is False]

    def has_mismatch(self) -> bool:
        return bool(self.mismatch_fields())


@dataclass(frozen=True)
class ReviewDecision:
    """Final conservative decision before it is attached to a record."""

    status: Status
    review_reason: ReviewReason | None = None
    confidence: Confidence | None = None
    detail: str = ""


@dataclass(frozen=True)
class VerificationRecord:
    """One email's classification and verification result."""

    email_id: str
    category: Category
    status: Status = "OK"
    review_reason: ReviewReason | None = None
    mismatch_fields: tuple[str, ...] = ()
    decided_by: DecisionMaker = "deterministic"

    @property
    def is_mismatch(self) -> bool:
        return self.status == "MISMATCH"
