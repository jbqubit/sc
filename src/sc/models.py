from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


NOTE_TYPES = ("vocab", "char", "sentence")
CARD_STATES = ("new", "learning", "review", "relearning")
GRADES = ("again", "hard", "good", "easy")


@dataclass(slots=True)
class ScheduleResult:
    reviewed_at: datetime
    state_after: str
    due_after: str
    interval_after: float
    ease_after: float
    step_index_after: int
    lapses_delta: int


@dataclass(slots=True)
class ImportResult:
    accepted: int = 0
    rejected: int = 0
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


def row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    return {key: row[key] for key in row.keys()}
