"""Assemble read-only API stories from pipeline traces and local fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from sdoc_verifier.pipeline import EmailRecord, load_emails, run_pipeline
from sdoc_verifier.trace import StepEvent, Trace


def _payload(event: StepEvent) -> dict[str, Any]:
    return cast("dict[str, Any]", event.payload or {})


def _safe_path(data_root: Path, relative: str) -> Path | None:
    candidate = (data_root / relative).resolve()
    if not candidate.is_relative_to(data_root.resolve()):
        return None
    return candidate


def _text_lines(data_root: Path, relative: str) -> list[str]:
    path = _safe_path(data_root, relative)
    if path is None or not path.is_file():
        return [f"attachment unavailable: {relative}"]
    if path.suffix.lower() not in (".txt", ".md", ""):
        return ["binary document; parsed rows are shown in the trace"]
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def build_story(
    email_id: str,
    record_payload: dict[str, Any],
    trace: Trace,
    email: EmailRecord,
    data_root: Path,
) -> dict[str, Any]:
    """Build one JSON-ready story without re-deriving pipeline evidence."""
    classify = trace.stage("classify")
    parse_events = [event for event in trace.events if event.stage == "parse"]
    extract_event = trace.stage("extract")
    compare_event = trace.stage("compare")
    review = trace.stage("review")

    anchors_by_path: dict[str, dict[str, Any]] = {}
    if extract_event is not None:
        for document in _payload(extract_event).get("documents", []):
            if isinstance(document, dict):
                anchors_by_path[str(document.get("path", ""))] = document

    attachments: list[dict[str, Any]] = []
    for relative in email.attachments:
        parse_event = next(
            (
                event
                for event in parse_events
                if (event.payload or {}).get("path") == relative
            ),
            None,
        )
        provenance = anchors_by_path.get(relative, {})
        field_anchors = cast("dict[str, dict[str, Any]]", provenance.get("fields", {}))
        raw_rows = (parse_event.payload or {}).get("rows") if parse_event else None
        lines = (
            [str(row) for row in raw_rows]
            if isinstance(raw_rows, list)
            else _text_lines(data_root, relative)
        )
        if parse_event is not None and parse_event.decision == "UNREADABLE":
            lines = [f"unreadable: {parse_event.detail}"]
        attachments.append(
            {
                "path": relative,
                "kind": provenance.get("kind")
                or (parse_event.decision if parse_event else "UNKNOWN"),
                "scanned": bool(provenance.get("scanned")),
                "translated": bool(provenance.get("translated")),
                "lines": lines,
                "anchors": {
                    name: meta.get("rows", [])
                    for name, meta in field_anchors.items()
                    if meta.get("present")
                },
            }
        )

    comparison = _payload(compare_event).get("fields") if compare_event else None
    return {
        "email_id": email_id,
        "subject": email.subject,
        "body": email.body,
        "classification": {
            "category": record_payload["category"],
            "confidence": classify.confidence.score
            if classify and classify.confidence
            else None,
            "reason": classify.detail if classify else "",
        },
        "attachments": attachments,
        "comparison": comparison,
        "verdict": {
            "status": record_payload["status"],
            "review_reason": record_payload["review_reason"],
            "mismatch_fields": list(record_payload["mismatch_fields"]),
            "decided_by": record_payload["decided_by"],
            "detail": review.detail if review else "",
        },
        "steps": [
            {"stage": event.stage, "decision": event.decision, "detail": event.detail}
            for event in trace.events
        ],
    }


def run_demo(
    data_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[Trace]]:
    """Run the deterministic local demo once and return API-ready state."""
    emails = load_emails(data_root)
    records, traces = run_pipeline(emails, data_root=data_root)
    records_out: list[dict[str, Any]] = []
    stories: dict[str, dict[str, Any]] = {}
    for record, trace in zip(records, traces, strict=True):
        payload = {
            "category": record.category,
            "status": record.status,
            "review_reason": record.review_reason,
            "mismatch_fields": list(record.mismatch_fields),
            "decided_by": record.decided_by,
        }
        records_out.append({"email_id": record.email_id, **payload})
        email = next(item for item_id, item in emails if item_id == record.email_id)
        stories[record.email_id] = build_story(
            record.email_id, payload, trace, email, data_root
        )
    return records_out, stories, traces


def load_subjects(data_root: Path) -> dict[str, str]:
    subjects: dict[str, str] = {}
    for email_id, email in load_emails(data_root):
        subjects[email_id] = email.subject
    return subjects


__all__ = ["build_story", "load_subjects", "run_demo"]
