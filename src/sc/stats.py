from __future__ import annotations

from sc.render import render_summary_table


def render_summary(stats: dict) -> None:
    render_summary_table(
        "Summary",
        ("Metric", "Value"),
        [
            ("Notes", stats["notes"]),
            ("Active Notes", stats["active_notes"]),
            ("Cards", stats["cards"]),
            ("Due Cards", stats["due_cards"]),
            ("Reviews Today", stats["reviews_today"]),
        ],
    )


def render_note_stats(rows: list[dict]) -> None:
    render_summary_table(
        "Notes By Type",
        ("Type", "Archived", "Count"),
        [(row["note_type"], "yes" if row["is_archived"] else "no", row["count"]) for row in rows],
    )


def render_card_stats(rows: list[dict]) -> None:
    render_summary_table(
        "Cards By Type/State",
        ("Type", "State", "Count"),
        [(row["note_type"], row["state"], row["count"]) for row in rows],
    )


def render_daily_stats(rows: list[dict]) -> None:
    render_summary_table(
        "Daily Reviews",
        ("Day", "Review Count"),
        [(row["day"], row["review_count"]) for row in rows],
    )
