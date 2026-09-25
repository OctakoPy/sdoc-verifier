"""Local read-only FastAPI service for the fictional SDOC demo."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.overview import build_overview
from api.story import load_subjects, run_demo
from api.subsets import derive_subsets, subset_tags

app = FastAPI(
    title="SDOC Verifier",
    version="0.1.0",
    description="Read-only local views over deterministic fictional shipping examples.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["GET"],
)


@dataclass(frozen=True)
class DemoState:
    records: list[dict[str, Any]] = field(default_factory=list)
    stories: dict[str, dict[str, Any]] = field(default_factory=dict)
    subjects: dict[str, str] = field(default_factory=dict)
    subsets: dict[str, list[str]] = field(default_factory=dict)
    tags: dict[str, list[str]] = field(default_factory=dict)
    error: str | None = None


@lru_cache(maxsize=1)
def _state() -> DemoState:
    root = Path(os.environ.get("SDOC_DATA_ROOT", "demo"))
    try:
        records, stories, _ = run_demo(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        return DemoState(error=str(exc))
    return DemoState(
        records=records,
        stories=stories,
        subjects=load_subjects(root),
        subsets=derive_subsets(records),
        tags=subset_tags(records),
    )


def _available() -> DemoState:
    state = _state()
    if state.error is not None:
        raise HTTPException(503, state.error)
    return state


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "deterministic",
        "read_only": True,
        "dataset": "fictional demo",
    }


@app.get("/api/overview")
def overview() -> dict[str, object]:
    return build_overview(_available().records)


@app.get("/api/subsets")
def subsets() -> dict[str, list[str]]:
    return _available().subsets


@app.get("/api/emails")
def emails(subset: str | None = None) -> dict[str, object]:
    state = _available()
    members: set[str] | None = None
    if subset is not None:
        if subset not in state.subsets:
            raise HTTPException(404, f"unknown filter: {subset}")
        members = set(state.subsets[subset])
    items = [
        {
            "email_id": record["email_id"],
            "subject": state.subjects.get(str(record["email_id"]), ""),
            "category": record["category"],
            "status": record["status"],
            "review_reason": record["review_reason"],
            "mismatch_fields": record["mismatch_fields"],
            "decided_by": record["decided_by"],
            "filters": state.tags.get(str(record["email_id"]), []),
            "classification_reason": next(
                (
                    story["classification"]["reason"]
                    for story in state.stories.values()
                    if story["email_id"] == record["email_id"]
                ),
                "",
            ),
        }
        for record in state.records
        if members is None or str(record["email_id"]) in members
    ]
    return {"count": len(items), "emails": items}


@app.get("/api/emails/{email_id}/story")
def story(email_id: str) -> dict[str, object]:
    state = _available()
    try:
        return state.stories[email_id]
    except KeyError as exc:
        raise HTTPException(404, f"unknown email: {email_id}") from exc


__all__ = ["app"]
