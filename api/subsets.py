"""Deterministic filters derived from the current local result set."""

from __future__ import annotations

from typing import Any


def derive_subsets(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    ordered_ids = [str(record["email_id"]) for record in records]
    return {
        "starter": ordered_ids[: min(8, len(ordered_ids))],
        "comparisons": [
            str(record["email_id"])
            for record in records
            if record["category"] == "BL_COMPARISON"
        ],
        "needs_review": [
            str(record["email_id"])
            for record in records
            if record["status"] == "NEEDS_REVIEW"
        ],
        "mismatches": [
            str(record["email_id"])
            for record in records
            if record["status"] == "MISMATCH"
        ],
        "all": ordered_ids,
    }


def subset_tags(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    tags = {str(record["email_id"]): [] for record in records}
    for name, members in derive_subsets(records).items():
        for email_id in members:
            tags.setdefault(email_id, []).append(name)
    return tags


__all__ = ["derive_subsets", "subset_tags"]
