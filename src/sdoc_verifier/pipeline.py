"""Orchestrate classification, parsing, extraction, comparison, and review."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sdoc_verifier.classify import classify_email
from sdoc_verifier.extract import extract_fields_anchored
from sdoc_verifier.models import (
    FIELDS,
    ComparisonResult,
    ExtractedFields,
    ParsedDocument,
    VerificationRecord,
)
from sdoc_verifier.parsers import parse_attachment
from sdoc_verifier.review import review_comparison
from sdoc_verifier.trace import StepEvent, Trace


class EmailLike(Protocol):
    @property
    def subject(self) -> str | None: ...

    @property
    def body(self) -> str: ...


@dataclass(frozen=True)
class EmailRecord:
    email_id: str
    subject: str
    body: str
    attachments: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> EmailRecord:
        raw_attachments = payload.get("attachments", [])
        attachments = (
            tuple(str(item) for item in raw_attachments)
            if isinstance(raw_attachments, list)
            else ()
        )
        return cls(
            email_id=str(payload.get("email_id", "")),
            subject=str(payload.get("subject", "")),
            body=str(payload.get("body", "")),
            attachments=attachments,
        )


def _iter_records(
    emails: Iterable[tuple[str, EmailLike]],
    *,
    data_root: Path | None,
    gemini_keys: list[str] | None,
) -> Iterator[tuple[VerificationRecord, Trace]]:
    for email_id, email in emails:
        trace = Trace(email_id=email_id)
        category, confidence = classify_email(email)
        trace.append(
            StepEvent(
                stage="classify",
                decision=category,
                confidence=confidence,
                detail=confidence.reason,
            )
        )
        if category != "BL_COMPARISON":
            yield VerificationRecord(email_id=email_id, category=category), trace
            continue
        record, trace = _comparison_flow(
            email_id=email_id,
            email=email,
            trace=trace,
            data_root=data_root,
            gemini_keys=gemini_keys or [],
        )
        yield record, trace


def _unreadable(path: str, error: str) -> ParsedDocument:
    return ParsedDocument(
        path=path,
        fmt="unknown",
        kind="UNREADABLE",
        error=error,
    )


def _safe_attachment(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("attachment path escapes data root")
    return candidate


def _comparison_flow(
    *,
    email_id: str,
    email: EmailLike,
    trace: Trace,
    data_root: Path | None,
    gemini_keys: list[str],
) -> tuple[VerificationRecord, Trace]:
    attachments = list(getattr(email, "attachments", []) or [])
    documents: list[ParsedDocument] = []
    for relative in attachments:
        document: ParsedDocument
        confidence = None
        if data_root is None:
            document = _unreadable(relative, "no local data root configured")
        else:
            try:
                path = _safe_attachment(data_root, relative)
                data = path.read_bytes()
                document, confidence = parse_attachment(
                    relative, data, gemini_keys=gemini_keys
                )
            except (OSError, ValueError) as exc:
                document = _unreadable(relative, str(exc))
        payload: dict[str, object] = {"path": relative}
        if document.rows:
            payload["rows"] = list(document.rows)
        trace.append(
            StepEvent(
                stage="parse",
                decision=document.kind,
                confidence=confidence,
                detail=confidence.reason
                if confidence
                else document.error or "unreadable",
                payload=payload,
            )
        )
        documents.append(document)

    decision, comparison = review_comparison(len(attachments), documents)
    _append_provenance_events(trace, documents, comparison)
    trace.append(
        StepEvent(
            stage="review",
            decision=decision.status,
            detail=decision.detail,
        )
    )
    mismatch_fields = (
        tuple(comparison.mismatch_fields())
        if decision.status == "MISMATCH" and comparison is not None
        else ()
    )
    assisted = any(
        document.kind != "UNREADABLE" and (document.scanned or document.translated)
        for document in documents
    )
    record = VerificationRecord(
        email_id=email_id,
        category="BL_COMPARISON",
        status=decision.status,
        review_reason=decision.review_reason,
        mismatch_fields=mismatch_fields,
        decided_by="gemini" if assisted else "deterministic",
    )
    return record, trace


def _provenance_payload(
    fields: ExtractedFields,
    anchors: dict[str, list[int]],
    document: ParsedDocument,
) -> dict[str, object]:
    return {
        "path": document.path,
        "kind": document.kind,
        "scanned": document.scanned,
        "translated": document.translated,
        "fields": {
            name: {
                "rows": anchors.get(name, []),
                "present": bool(getattr(fields, name).strip()),
            }
            for name in FIELDS
        },
    }


def _comparison_payload(comparison: ComparisonResult) -> dict[str, object]:
    return {
        "fields": {
            name: {
                "si": comparison.values.get(name, ("", ""))[0],
                "bl": comparison.values.get(name, ("", ""))[1],
                "match": comparison.field_matches.get(name),
            }
            for name in FIELDS
        }
    }


def _append_provenance_events(
    trace: Trace,
    documents: list[ParsedDocument],
    comparison: ComparisonResult | None,
) -> None:
    if not documents:
        return
    trace.append(
        StepEvent(
            stage="extract",
            decision="EXTRACTED",
            payload={
                "documents": [
                    _provenance_payload(*extract_fields_anchored(document), document)
                    for document in documents
                ]
            },
        )
    )
    if comparison is not None:
        trace.append(
            StepEvent(
                stage="compare",
                decision="MISMATCH" if comparison.has_mismatch() else "OK",
                payload=_comparison_payload(comparison),
            )
        )


def load_emails(data_root: str | Path) -> list[tuple[str, EmailRecord]]:
    """Load fictional or authorized inbox records from a local data root."""
    inbox = Path(data_root) / "inbox"
    if not inbox.is_dir():
        raise FileNotFoundError(f"no inbox directory under {data_root}")
    emails: list[tuple[str, EmailRecord]] = []
    for path in sorted(inbox.glob("email_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"inbox record must be an object: {path}")
        email = EmailRecord.from_payload(payload)
        if not email.email_id:
            raise ValueError(f"inbox record has no email_id: {path}")
        emails.append((email.email_id, email))
    return emails


def run_pipeline(
    emails: Iterable[tuple[str, EmailLike]],
    *,
    data_root: str | Path | None = None,
    gemini_keys: list[str] | None = None,
) -> tuple[list[VerificationRecord], list[Trace]]:
    """Run the complete read-only pipeline over email records in input order."""
    root = Path(data_root) if data_root is not None else None
    records: list[VerificationRecord] = []
    traces: list[Trace] = []
    for record, trace in _iter_records(emails, data_root=root, gemini_keys=gemini_keys):
        records.append(record)
        traces.append(trace)
    return records, traces


__all__ = [
    "EmailLike",
    "EmailRecord",
    "load_emails",
    "run_pipeline",
]
