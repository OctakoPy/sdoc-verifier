"""Structured per-email decision traces."""

from __future__ import annotations

from dataclasses import dataclass, field

from sdoc_verifier.models import Confidence


@dataclass(frozen=True)
class StepEvent:
    stage: str
    decision: str
    confidence: Confidence | None = None
    detail: str = ""
    payload: dict[str, object] | None = None


@dataclass
class Trace:
    email_id: str
    events: list[StepEvent] = field(default_factory=list)

    def append(self, event: StepEvent) -> None:
        self.events.append(event)

    def stage(self, stage: str) -> StepEvent | None:
        return next((event for event in self.events if event.stage == stage), None)


__all__ = ["StepEvent", "Trace"]
