from __future__ import annotations

from rich.console import Console

from src.db import connect
from src.repository import Repository
from src.review_session import ReviewSession


class ScriptedIO:
    def __init__(self, reveal_keys: list[str], grades: list[str]) -> None:
        self._reveals = iter(reveal_keys)
        self._grades = iter(grades)

    def wait_for_reveal(self) -> str:
        return next(self._reveals)

    def read_grade(self) -> str:
        return next(self._grades)


def test_review_session_updates_cards_and_logs_reviews(tmp_path):
    repo = Repository(connect(tmp_path / "review.db"))
    note_id = repo.create_note(
        "vocab",
        {
            "hanzi": "学校",
            "pinyin": "xue2 xiao4",
            "english": "school",
            "tags": "hsk1",
            "source": "manual",
        },
    )
    note = repo.get_note(note_id)
    assert note is not None
    card_id = note["cards"][0]["id"]

    session = ReviewSession(repo, io=ScriptedIO([" "], ["good"]), console=Console(record=True))
    result = session.run(limit=1)

    assert result["reviewed"] == 1
    card = repo.get_card(card_id)
    assert card is not None
    assert card["state"] == "learning"
    review_count = repo.conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    assert review_count == 1
