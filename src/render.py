from __future__ import annotations

import os
import sys
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cardgen import build_cloze


console = Console()


def render_prompt(card: dict, index: int, total: int) -> None:
    prompt = _prompt_text(card)
    header = f"{card['note_type']} [{index}/{total}] {card['card_type']}"
    console.print(Panel(prompt, title=header, border_style="cyan"))
    console.print("[dim]Press space or enter to reveal. Press q to quit.[/dim]")


def render_reveal(card: dict) -> None:
    note = card["note"]
    table = Table(title="Answer", show_header=False, box=None)
    if card["card_type"] == "hanzi_to_meaning":
        table.add_row("Pinyin", note["pinyin"])
        table.add_row("Meaning", note["english"])
        _maybe_add(table, "Example CN", note.get("example_cn", ""))
        _maybe_add(table, "Example EN", note.get("example_en", ""))
    elif card["card_type"] == "english_to_hanzi":
        table.add_row("Hanzi", note["hanzi"])
        table.add_row("Pinyin", note["pinyin"])
        _maybe_add(table, "Example CN", note.get("example_cn", ""))
        _maybe_add(table, "Example EN", note.get("example_en", ""))
    elif card["card_type"] == "char_to_meaning":
        table.add_row("Pinyin", note.get("pinyin", ""))
        table.add_row("Meaning", note["english"])
        _maybe_add(table, "Components", note.get("components", ""))
        _maybe_add(table, "Mnemonic", note.get("mnemonic", ""))
    elif card["card_type"] == "meaning_to_char":
        table.add_row("Hanzi", note["hanzi"])
        _maybe_add(table, "Pinyin", note.get("pinyin", ""))
        _maybe_add(table, "Components", note.get("components", ""))
        _maybe_add(table, "Mnemonic", note.get("mnemonic", ""))
    elif card["card_type"] == "sentence_to_meaning":
        _maybe_add(table, "Pinyin", note.get("sentence_pinyin", ""))
        table.add_row("Meaning", note["sentence_en"])
        _maybe_add(table, "Focus", note.get("focus_term", ""))
    elif card["card_type"] == "cloze_focus_term":
        table.add_row("Focus", note["focus_term"])
        table.add_row("Sentence", note["sentence_cn"])
        _maybe_add(table, "Pinyin", note.get("sentence_pinyin", ""))
        table.add_row("Meaning", note["sentence_en"])
    console.print(table)
    console.print("[bold]1[/bold] again  [bold]2[/bold] hard  [bold]3[/bold] good  [bold]4[/bold] easy")


def render_note(note: dict) -> None:
    table = Table(title=f"Note {note['id']}", show_header=False, box=None)
    table.add_row("Type", note["note_type"])
    table.add_row("Tags", note["tags"])
    table.add_row("Source", note["source"])
    for key, value in note.items():
        if key in {"id", "note_type", "tags", "source", "cards", "created_at", "updated_at", "is_archived", "note_id", "tag_list"}:
            continue
        if value != "":
            table.add_row(key, str(value))
    table.add_row("Archived", "yes" if note["is_archived"] else "no")
    console.print(table)
    if note["cards"]:
        cards = Table(title="Cards")
        cards.add_column("ID")
        cards.add_column("Type")
        cards.add_column("State")
        cards.add_column("Due")
        for card in note["cards"]:
            cards.add_row(str(card["id"]), card["card_type"], card["state"], card["due_at"] or "-")
        console.print(cards)


def render_card(card: dict) -> None:
    table = Table(title=f"Card {card['id']}", show_header=False, box=None)
    for label in ("card_type", "state", "due_at", "interval_days", "ease_factor", "lapses", "review_count", "suspended"):
        table.add_row(label, str(card.get(label, "")))
    console.print(table)
    render_note(card["note"])


def render_summary_table(title: str, columns: Iterable[str], rows: Iterable[Iterable[str]]) -> None:
    table = Table(title=title)
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*[str(value) for value in row])
    console.print(table)


def read_key() -> str:
    if os.name == "nt":
        import msvcrt

        char = msvcrt.getwch()
        return "\n" if char == "\r" else char
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return char


def _prompt_text(card: dict) -> str:
    note = card["note"]
    if card["card_type"] == "hanzi_to_meaning":
        return note["hanzi"]
    if card["card_type"] == "english_to_hanzi":
        return note["english"]
    if card["card_type"] == "char_to_meaning":
        return note["hanzi"]
    if card["card_type"] == "meaning_to_char":
        return note["english"]
    if card["card_type"] == "sentence_to_meaning":
        return note["sentence_cn"]
    if card["card_type"] == "cloze_focus_term":
        return build_cloze(note["sentence_cn"], note["focus_term"])
    return ""


def _maybe_add(table: Table, label: str, value: str) -> None:
    if value:
        table.add_row(label, value)
