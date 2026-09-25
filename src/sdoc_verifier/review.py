"""Conservative review decisions for parsed SI/BL pairs."""

from __future__ import annotations

from sdoc_verifier.compare import compare_fields
from sdoc_verifier.extract import extract_fields
from sdoc_verifier.models import (
    FIELDS,
    ComparisonResult,
    ExtractedFields,
    ParsedDocument,
    ReviewDecision,
    Status,
)


def _blank_fields(*field_sets: ExtractedFields) -> list[str]:
    return [
        name
        for name in FIELDS
        if any(not getattr(fields, name).strip() for fields in field_sets)
    ]


def review_comparison(
    attachment_count: int,
    documents: list[ParsedDocument],
) -> tuple[ReviewDecision, ComparisonResult | None]:
    """Return a review result without guessing around incomplete evidence."""
    if attachment_count < 2:
        return (
            ReviewDecision(
                status="NEEDS_REVIEW",
                review_reason="missing_attachment",
                detail=(
                    f"{attachment_count} attachment(s) present; "
                    "SI and draft BL are required"
                ),
            ),
            None,
        )

    if any(document.kind == "OTHER" for document in documents):
        paths = ", ".join(
            document.path for document in documents if document.kind == "OTHER"
        )
        return (
            ReviewDecision(
                status="NEEDS_REVIEW",
                review_reason="wrong_doc_type",
                detail=f"not SI/BL: {paths}",
            ),
            None,
        )

    if any(document.kind == "UNREADABLE" for document in documents):
        paths = ", ".join(
            document.path for document in documents if document.kind == "UNREADABLE"
        )
        return (
            ReviewDecision(
                status="NEEDS_REVIEW",
                review_reason="unreadable",
                detail=f"unreadable document(s): {paths}",
            ),
            None,
        )

    si_documents = [document for document in documents if document.kind == "SI"]
    bl_documents = [document for document in documents if document.kind == "BL"]
    if len(si_documents) != 1 or len(bl_documents) != 1:
        return (
            ReviewDecision(
                status="NEEDS_REVIEW",
                review_reason="wrong_doc_type",
                detail="could not identify exactly one SI and one draft BL",
            ),
            None,
        )

    si_fields = extract_fields(si_documents[0])
    bl_fields = extract_fields(bl_documents[0])
    blank_fields = _blank_fields(si_fields, bl_fields)
    if blank_fields:
        return (
            ReviewDecision(
                status="NEEDS_REVIEW",
                review_reason="missing_value",
                detail=f"missing required value(s): {', '.join(blank_fields)}",
            ),
            None,
        )

    comparison = compare_fields(si_fields, bl_fields)
    mismatches = comparison.mismatch_fields()
    status: Status = "MISMATCH" if mismatches else "OK"
    detail = (
        f"mismatched field(s): {', '.join(mismatches)}"
        if mismatches
        else "all seven fields match after normalization"
    )
    return ReviewDecision(status=status, detail=detail), comparison


__all__ = ["review_comparison"]
