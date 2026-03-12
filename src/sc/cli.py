from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sc.config import resolve_db_path
from sc.db import connect
from sc.importers import import_csv
from sc.render import console, render_card, render_note, render_summary_table
from sc.repository import Repository
from sc.review_session import ReviewSession
from sc.stats import render_card_stats, render_daily_stats, render_note_stats, render_summary


app = typer.Typer(help="Standalone Chinese flashcard CLI.")
add_app = typer.Typer(help="Add new notes.")
import_app = typer.Typer(help="Import notes from CSV.")
list_app = typer.Typer(help="List notes and cards.")
show_app = typer.Typer(help="Show a note or card.")
edit_app = typer.Typer(help="Edit existing notes.")
stats_app = typer.Typer(help="Show review statistics.")
suspend_app = typer.Typer(help="Suspend entities.")
unsuspend_app = typer.Typer(help="Unsuspend entities.")
archive_app = typer.Typer(help="Archive entities.")
restore_app = typer.Typer(help="Restore entities.")

app.add_typer(add_app, name="add")
app.add_typer(import_app, name="import")
app.add_typer(list_app, name="list")
app.add_typer(show_app, name="show")
app.add_typer(edit_app, name="edit")
app.add_typer(stats_app, name="stats")
app.add_typer(suspend_app, name="suspend")
app.add_typer(unsuspend_app, name="unsuspend")
app.add_typer(archive_app, name="archive")
app.add_typer(restore_app, name="restore")

DBOption = Annotated[Path | None, typer.Option("--db", help="SQLite database path.")]


def get_repo(db_path: Path | None) -> Repository:
    return Repository(connect(resolve_db_path(db_path)))


@app.command()
def init(db: DBOption = None) -> None:
    path = resolve_db_path(db)
    connect(path).close()
    console.print(f"Initialized database at {path}")


@add_app.command("vocab")
def add_vocab(db: DBOption = None) -> None:
    repo = get_repo(db)
    note_id = repo.create_note(
        "vocab",
        {
            "hanzi": typer.prompt("Hanzi"),
            "pinyin": typer.prompt("Pinyin"),
            "english": typer.prompt("English"),
            "example_cn": typer.prompt("Example CN", default=""),
            "example_en": typer.prompt("Example EN", default=""),
            "tags": typer.prompt("Tags (comma-separated)", default=""),
            "source": typer.prompt("Source", default=""),
        },
    )
    console.print(f"Created vocab note {note_id}")


@add_app.command("char")
def add_char(db: DBOption = None) -> None:
    repo = get_repo(db)
    note_id = repo.create_note(
        "char",
        {
            "hanzi": typer.prompt("Character"),
            "pinyin": typer.prompt("Pinyin", default=""),
            "english": typer.prompt("English"),
            "components": typer.prompt("Components", default=""),
            "mnemonic": typer.prompt("Mnemonic", default=""),
            "example_cn": typer.prompt("Example CN", default=""),
            "example_en": typer.prompt("Example EN", default=""),
            "tags": typer.prompt("Tags (comma-separated)", default=""),
            "source": typer.prompt("Source", default=""),
        },
    )
    console.print(f"Created char note {note_id}")


@add_app.command("sentence")
def add_sentence(db: DBOption = None) -> None:
    repo = get_repo(db)
    note_id = repo.create_note(
        "sentence",
        {
            "sentence_cn": typer.prompt("Sentence CN"),
            "sentence_pinyin": typer.prompt("Sentence Pinyin", default=""),
            "sentence_en": typer.prompt("Sentence EN"),
            "focus_term": typer.prompt("Focus Term", default=""),
            "notes": typer.prompt("Notes", default=""),
            "tags": typer.prompt("Tags (comma-separated)", default=""),
            "source": typer.prompt("Source", default=""),
        },
    )
    console.print(f"Created sentence note {note_id}")


@import_app.command("vocab")
def import_vocab(path: Path, delimiter: str = ",", db: DBOption = None) -> None:
    repo = get_repo(db)
    result = import_csv(repo, "vocab", path, delimiter)
    _print_import_result(result)


@import_app.command("char")
def import_char(path: Path, delimiter: str = ",", db: DBOption = None) -> None:
    repo = get_repo(db)
    result = import_csv(repo, "char", path, delimiter)
    _print_import_result(result)


@import_app.command("sentence")
def import_sentence(path: Path, delimiter: str = ",", db: DBOption = None) -> None:
    repo = get_repo(db)
    result = import_csv(repo, "sentence", path, delimiter)
    _print_import_result(result)


@app.command()
def review(
    note_type: Annotated[str | None, typer.Option("--type", help="Filter by note type.")] = None,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by tag.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", help="Limit cards in this session.")] = None,
    new: Annotated[bool, typer.Option("--new", help="Review only new cards.")] = False,
    due: Annotated[bool, typer.Option("--due", help="Review only scheduled due cards.")] = False,
    db: DBOption = None,
) -> None:
    if new and due:
        raise typer.BadParameter("Use only one of --new or --due.")
    mode = "new" if new else "due" if due else "all"
    repo = get_repo(db)
    ReviewSession(repo).run(note_type=note_type, tag=tag, limit=limit, mode=mode)


@list_app.command("notes")
def list_notes(
    note_type: Annotated[str | None, typer.Option("--type", help="Filter by note type.")] = None,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by tag.")] = None,
    limit: Annotated[int, typer.Option("--limit", help="Maximum notes to display.")] = 50,
    db: DBOption = None,
) -> None:
    repo = get_repo(db)
    rows = repo.list_notes(note_type=note_type, tag=tag, limit=limit)
    render_summary_table(
        "Notes",
        ("ID", "Type", "Prompt", "Tags", "Source", "Cards", "Archived"),
        [
            (
                row["id"],
                row["note_type"],
                row["prompt_preview"],
                row["tags"],
                row["source"],
                row["card_count"],
                "yes" if row["is_archived"] else "no",
            )
            for row in rows
        ],
    )


@list_app.command("cards")
def list_cards(
    note_type: Annotated[str | None, typer.Option("--type", help="Filter by note type.")] = None,
    state: Annotated[str | None, typer.Option("--state", help="Filter by card state.")] = None,
    due: Annotated[bool, typer.Option("--due", help="Show only due cards.")] = False,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by tag.")] = None,
    limit: Annotated[int, typer.Option("--limit", help="Maximum cards to display.")] = 50,
    db: DBOption = None,
) -> None:
    repo = get_repo(db)
    rows = repo.list_cards(note_type=note_type, state=state, due_only=due, tag=tag, limit=limit)
    render_summary_table(
        "Cards",
        ("ID", "Note", "Type", "State", "Due", "Preview"),
        [(row["id"], row["note_id"], row["card_type"], row["state"], row["due_at"] or "-", row["prompt_preview"]) for row in rows],
    )


@list_app.command("due")
def list_due(
    note_type: Annotated[str | None, typer.Option("--type", help="Filter by note type.")] = None,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter by tag.")] = None,
    limit: Annotated[int, typer.Option("--limit", help="Maximum cards to display.")] = 50,
    db: DBOption = None,
) -> None:
    repo = get_repo(db)
    rows = repo.list_cards(note_type=note_type, tag=tag, due_only=True, limit=limit)
    render_summary_table(
        "Due Cards",
        ("ID", "Note", "Type", "State", "Due", "Preview"),
        [(row["id"], row["note_id"], row["card_type"], row["state"], row["due_at"] or "-", row["prompt_preview"]) for row in rows],
    )


@show_app.command("note")
def show_note(note_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    note = repo.get_note(note_id)
    if not note:
        raise typer.BadParameter(f"Note {note_id} not found.")
    render_note(note)


@show_app.command("card")
def show_card(card_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    card = repo.get_card(card_id)
    if not card:
        raise typer.BadParameter(f"Card {card_id} not found.")
    render_card(card)


@edit_app.command("note")
def edit_note(note_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    note = repo.get_note(note_id)
    if not note:
        raise typer.BadParameter(f"Note {note_id} not found.")
    payload = {"tags": typer.prompt("Tags", default=note["tags"]), "source": typer.prompt("Source", default=note["source"])}
    if note["note_type"] == "vocab":
        payload.update(
            {
                "hanzi": typer.prompt("Hanzi", default=note["hanzi"]),
                "pinyin": typer.prompt("Pinyin", default=note["pinyin"]),
                "english": typer.prompt("English", default=note["english"]),
                "example_cn": typer.prompt("Example CN", default=note.get("example_cn", "")),
                "example_en": typer.prompt("Example EN", default=note.get("example_en", "")),
            }
        )
    elif note["note_type"] == "char":
        payload.update(
            {
                "hanzi": typer.prompt("Character", default=note["hanzi"]),
                "pinyin": typer.prompt("Pinyin", default=note.get("pinyin", "")),
                "english": typer.prompt("English", default=note["english"]),
                "components": typer.prompt("Components", default=note.get("components", "")),
                "mnemonic": typer.prompt("Mnemonic", default=note.get("mnemonic", "")),
                "example_cn": typer.prompt("Example CN", default=note.get("example_cn", "")),
                "example_en": typer.prompt("Example EN", default=note.get("example_en", "")),
            }
        )
    else:
        payload.update(
            {
                "sentence_cn": typer.prompt("Sentence CN", default=note["sentence_cn"]),
                "sentence_pinyin": typer.prompt("Sentence Pinyin", default=note.get("sentence_pinyin", "")),
                "sentence_en": typer.prompt("Sentence EN", default=note["sentence_en"]),
                "focus_term": typer.prompt("Focus Term", default=note.get("focus_term", "")),
                "notes": typer.prompt("Notes", default=note.get("notes", "")),
            }
        )
    repo.update_note(note_id, payload)
    console.print(f"Updated note {note_id}")


@suspend_app.command("card")
def suspend_card(card_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    repo.suspend_card(card_id, True)
    console.print(f"Suspended card {card_id}")


@unsuspend_app.command("card")
def unsuspend_card(card_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    repo.suspend_card(card_id, False)
    console.print(f"Unsuspended card {card_id}")


@archive_app.command("note")
def archive_note(note_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    repo.archive_note(note_id, True)
    console.print(f"Archived note {note_id}")


@restore_app.command("note")
def restore_note(note_id: int, db: DBOption = None) -> None:
    repo = get_repo(db)
    repo.archive_note(note_id, False)
    console.print(f"Restored note {note_id}")


@stats_app.callback(invoke_without_command=True)
def stats_callback(ctx: typer.Context, db: DBOption = None) -> None:
    if ctx.invoked_subcommand:
        return
    repo = get_repo(db)
    render_summary(repo.summary_stats())


@stats_app.command("daily")
def stats_daily(days: Annotated[int, typer.Option("--days", help="Number of days to include.")] = 7, db: DBOption = None) -> None:
    repo = get_repo(db)
    render_daily_stats(repo.daily_review_stats(days))


@stats_app.command("cards")
def stats_cards(db: DBOption = None) -> None:
    repo = get_repo(db)
    render_card_stats(repo.card_stats())


@stats_app.command("notes")
def stats_notes(db: DBOption = None) -> None:
    repo = get_repo(db)
    render_note_stats(repo.note_stats())


def _print_import_result(result: object) -> None:
    accepted = getattr(result, "accepted")
    rejected = getattr(result, "rejected")
    errors = getattr(result, "errors")
    console.print(f"Imported {accepted} row(s); rejected {rejected} row(s).")
    for error in errors[:10]:
        console.print(f"[red]{error}[/red]")


if __name__ == "__main__":
    app()
