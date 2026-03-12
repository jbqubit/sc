from __future__ import annotations

from rich.console import Console

from src.render import read_key, render_prompt, render_reveal
from src.repository import Repository
from src.scheduler import schedule


GRADE_KEYS = {"1": "again", "2": "hard", "3": "good", "4": "easy"}


class ReviewIO:
    def wait_for_reveal(self) -> str:
        return read_key()

    def read_grade(self) -> str:
        while True:
            key = read_key()
            if key in GRADE_KEYS:
                return GRADE_KEYS[key]
            if key.lower() == "q":
                return "quit"


class ReviewSession:
    def __init__(self, repo: Repository, io: ReviewIO | None = None, console: Console | None = None) -> None:
        self.repo = repo
        self.io = io or ReviewIO()
        self.console = console or Console()

    def run(
        self,
        note_type: str | None = None,
        tag: str | None = None,
        limit: int | None = None,
        mode: str = "all",
    ) -> dict[str, int]:
        cards = self.repo.get_review_cards(note_type=note_type, tag=tag, limit=limit, mode=mode)
        if not cards:
            self.console.print("No cards available for review.")
            return {"reviewed": 0}

        reviewed = 0
        total = len(cards)
        for index, card in enumerate(cards, start=1):
            render_prompt(card, index, total)
            reveal_key = self.io.wait_for_reveal()
            if reveal_key.lower() == "q":
                break
            render_reveal(card)
            grade = self.io.read_grade()
            if grade == "quit":
                break
            result = schedule(card, grade)
            self.repo.apply_review(card["id"], grade, result)
            reviewed += 1
            self.console.print()
        self.console.print(f"Reviewed {reviewed} card(s).")
        return {"reviewed": reviewed}
