from __future__ import annotations

from datetime import UTC, datetime

from src.scheduler import parse_utc_iso, schedule


NOW = datetime(2026, 3, 12, 12, 0, tzinfo=UTC)


def test_new_card_good_moves_to_second_learning_step():
    result = schedule({"state": "new", "step_index": 0, "interval_days": 0, "ease_factor": 2.5}, "good", NOW)
    assert result.state_after == "learning"
    assert parse_utc_iso(result.due_after) == datetime(2026, 3, 12, 12, 10, tzinfo=UTC)
    assert result.step_index_after == 1


def test_learning_good_graduates_after_last_step():
    result = schedule({"state": "learning", "step_index": 1, "interval_days": 0, "ease_factor": 2.5}, "good", NOW)
    assert result.state_after == "review"
    assert result.interval_after == 1.0


def test_review_again_moves_to_relearning():
    result = schedule({"state": "review", "step_index": 0, "interval_days": 8, "ease_factor": 2.5}, "again", NOW)
    assert result.state_after == "relearning"
    assert result.interval_after == 2.0
    assert result.lapses_delta == 1


def test_review_easy_expands_interval_and_ease():
    result = schedule({"state": "review", "step_index": 0, "interval_days": 5, "ease_factor": 2.5}, "easy", NOW)
    assert result.state_after == "review"
    assert result.interval_after == 16.25
    assert result.ease_after == 2.65
