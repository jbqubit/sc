from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.models import GRADES, ScheduleResult


LEARNING_STEPS_MINUTES = (1, 10)
RELEARNING_STEP_MINUTES = 10
MIN_EASE = 1.3
MAX_EASE = 3.0


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_utc_iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def clamp_ease(value: float) -> float:
    return max(MIN_EASE, min(MAX_EASE, value))


def schedule(card: dict, grade: str, reviewed_at: datetime | None = None) -> ScheduleResult:
    if grade not in GRADES:
        raise ValueError(f"Unsupported grade: {grade}")

    now = reviewed_at or utc_now()
    state = card["state"]
    current_step = int(card["step_index"])
    interval = float(card["interval_days"])
    ease = float(card["ease_factor"])

    if state == "new":
        return _schedule_learning(current_step=0, grade=grade, now=now, ease=ease)
    if state == "learning":
        return _schedule_learning(current_step=current_step, grade=grade, now=now, ease=ease)
    if state == "review":
        return _schedule_review(interval=interval, grade=grade, now=now, ease=ease)
    if state == "relearning":
        return _schedule_relearning(interval=interval, grade=grade, now=now, ease=ease)
    raise ValueError(f"Unsupported card state: {state}")


def _schedule_learning(current_step: int, grade: str, now: datetime, ease: float) -> ScheduleResult:
    if grade == "again":
        due = now + timedelta(minutes=LEARNING_STEPS_MINUTES[0])
        return ScheduleResult(now, "learning", to_utc_iso(due), 0.0, ease, 0, 0)
    if grade == "hard":
        due = now + timedelta(minutes=LEARNING_STEPS_MINUTES[1])
        return ScheduleResult(now, "learning", to_utc_iso(due), 0.0, ease, current_step, 0)
    if grade == "good":
        next_step = current_step + 1
        if next_step < len(LEARNING_STEPS_MINUTES):
            due = now + timedelta(minutes=LEARNING_STEPS_MINUTES[next_step])
            return ScheduleResult(now, "learning", to_utc_iso(due), 0.0, ease, next_step, 0)
        due = now + timedelta(days=1)
        return ScheduleResult(now, "review", to_utc_iso(due), 1.0, ease, 0, 0)
    due = now + timedelta(days=3)
    return ScheduleResult(now, "review", to_utc_iso(due), 3.0, ease, 0, 0)


def _schedule_review(interval: float, grade: str, now: datetime, ease: float) -> ScheduleResult:
    if grade == "again":
        reduced = max(1.0, interval * 0.25)
        due = now + timedelta(minutes=RELEARNING_STEP_MINUTES)
        return ScheduleResult(now, "relearning", to_utc_iso(due), reduced, clamp_ease(ease - 0.20), 0, 1)
    if grade == "hard":
        updated = max(interval + 1.0, interval * 1.2)
        due = now + timedelta(days=updated)
        return ScheduleResult(now, "review", to_utc_iso(due), updated, clamp_ease(ease - 0.15), 0, 0)
    if grade == "good":
        updated = max(interval + 1.0, interval * ease)
        due = now + timedelta(days=updated)
        return ScheduleResult(now, "review", to_utc_iso(due), updated, clamp_ease(ease), 0, 0)
    updated = max(interval + 2.0, interval * ease * 1.3)
    due = now + timedelta(days=updated)
    return ScheduleResult(now, "review", to_utc_iso(due), updated, clamp_ease(ease + 0.15), 0, 0)


def _schedule_relearning(interval: float, grade: str, now: datetime, ease: float) -> ScheduleResult:
    if grade == "again":
        due = now + timedelta(minutes=RELEARNING_STEP_MINUTES)
        return ScheduleResult(now, "relearning", to_utc_iso(due), interval, ease, 0, 0)
    if grade == "hard":
        due = now + timedelta(days=1)
        return ScheduleResult(now, "review", to_utc_iso(due), 1.0, clamp_ease(ease - 0.15), 0, 0)
    if grade == "good":
        updated = max(1.0, interval)
        due = now + timedelta(days=updated)
        return ScheduleResult(now, "review", to_utc_iso(due), updated, ease, 0, 0)
    updated = max(2.0, interval * 1.3)
    due = now + timedelta(days=updated)
    return ScheduleResult(now, "review", to_utc_iso(due), updated, clamp_ease(ease + 0.15), 0, 0)
