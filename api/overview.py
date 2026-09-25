"""Aggregate counts for the local fictional demo."""

from __future__ import annotations

from collections import Counter
from typing import Any

CATEGORIES = ("BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM")
STATUSES = ("OK", "MISMATCH", "NEEDS_REVIEW")
REASONS = ("wrong_doc_type", "missing_attachment", "unreadable", "missing_value")


def build_overview(records: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(record["category"] for record in records)
    status_counts = Counter(record["status"] for record in records)
    reason_counts = Counter(
        record["review_reason"] for record in records if record["review_reason"]
    )
    field_counts: Counter[str] = Counter()
    for record in records:
        if record["status"] == "MISMATCH":
            field_counts.update(record["mismatch_fields"])
    return {
        "dataset": {
            "label": "fictional demo",
            "validation": "synthetic, in-distribution examples",
        },
        "total_emails": len(records),
        "category_distribution": {
            category: category_counts.get(category, 0) for category in CATEGORIES
        },
        "status_distribution": {
            status: status_counts.get(status, 0) for status in STATUSES
        },
        "review_reasons": {reason: reason_counts.get(reason, 0) for reason in REASONS},
        "mismatches": {
            "email_count": status_counts.get("MISMATCH", 0),
            "field_counts": dict(field_counts.most_common()),
        },
    }


__all__ = ["CATEGORIES", "REASONS", "STATUSES", "build_overview"]
