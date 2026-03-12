from __future__ import annotations

import sqlite3
from typing import Any

from sc.cardgen import generate_cards
from sc.models import row_to_dict
from sc.scheduler import to_utc_iso, utc_now
from sc.validators import normalize_tags, validate_note_type, validate_payload


NOTE_TABLES = {
    "vocab": "vocab_notes",
    "char": "char_notes",
    "sentence": "sentence_notes",
}

NOTE_FIELDS = {
    "vocab": ("hanzi", "pinyin", "english", "example_cn", "example_en"),
    "char": ("hanzi", "pinyin", "english", "components", "mnemonic", "example_cn", "example_en"),
    "sentence": ("sentence_cn", "sentence_pinyin", "sentence_en", "focus_term", "notes"),
}


class Repository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_note(self, note_type: str, payload: dict[str, str]) -> int:
        cleaned = validate_payload(note_type, payload)
        now = to_utc_iso(utc_now())
        cursor = self.conn.execute(
            """
            INSERT INTO notes (note_type, tags, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (note_type, cleaned.get("tags", ""), cleaned.get("source", ""), now, now),
        )
        note_id = int(cursor.lastrowid)
        self._write_note_payload(note_id, note_type, cleaned)
        self._ensure_cards(note_id, note_type, cleaned, now)
        self.conn.commit()
        return note_id

    def update_note(self, note_id: int, payload: dict[str, str]) -> None:
        existing = self.get_note(note_id)
        if not existing:
            raise ValueError(f"Note {note_id} not found")
        note_type = existing["note_type"]
        cleaned = validate_payload(note_type, payload)
        now = to_utc_iso(utc_now())
        self.conn.execute(
            "UPDATE notes SET tags = ?, source = ?, updated_at = ? WHERE id = ?",
            (cleaned.get("tags", ""), cleaned.get("source", ""), now, note_id),
        )
        self._delete_note_payload(note_id, note_type)
        self._write_note_payload(note_id, note_type, cleaned)
        self._ensure_cards(note_id, note_type, cleaned, now)
        self.conn.commit()

    def _write_note_payload(self, note_id: int, note_type: str, payload: dict[str, str]) -> None:
        table = NOTE_TABLES[note_type]
        fields = NOTE_FIELDS[note_type]
        values = [payload.get(field, "") for field in fields]
        placeholders = ", ".join("?" for _ in fields)
        columns = ", ".join(fields)
        self.conn.execute(
            f"INSERT INTO {table} (note_id, {columns}) VALUES (?, {placeholders})",
            (note_id, *values),
        )

    def _delete_note_payload(self, note_id: int, note_type: str) -> None:
        table = NOTE_TABLES[note_type]
        self.conn.execute(f"DELETE FROM {table} WHERE note_id = ?", (note_id,))

    def _ensure_cards(self, note_id: int, note_type: str, payload: dict[str, str], now: str) -> None:
        current_types = {
            row["card_type"]
            for row in self.conn.execute("SELECT card_type FROM cards WHERE note_id = ?", (note_id,)).fetchall()
        }
        desired = generate_cards(note_type, payload)
        desired_types = {card["card_type"] for card in desired}
        for card_type in current_types - desired_types:
            self.conn.execute("DELETE FROM cards WHERE note_id = ? AND card_type = ?", (note_id, card_type))
        for card in desired:
            if card["card_type"] in current_types:
                continue
            self.conn.execute(
                """
                INSERT INTO cards (
                    note_id, card_type, prompt_lang, answer_lang, state,
                    due_at, step_index, interval_days, ease_factor, lapses,
                    review_count, suspended, last_reviewed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'new', NULL, 0, 0, 2.5, 0, 0, 0, NULL, ?, ?)
                """,
                (note_id, card["card_type"], card["prompt_lang"], card["answer_lang"], now, now),
            )

    def get_note(self, note_id: int) -> dict[str, Any] | None:
        note_row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if note_row is None:
            return None
        note = row_to_dict(note_row)
        detail = self.conn.execute(
            f"SELECT * FROM {NOTE_TABLES[note['note_type']]} WHERE note_id = ?",
            (note_id,),
        ).fetchone()
        if detail:
            note.update(row_to_dict(detail))
        cards = self.conn.execute(
            "SELECT * FROM cards WHERE note_id = ? ORDER BY id",
            (note_id,),
        ).fetchall()
        note["cards"] = [row_to_dict(card) for card in cards]
        note["tag_list"] = [tag for tag in note["tags"].split(",") if tag]
        return note

    def get_card(self, card_id: int) -> dict[str, Any] | None:
        card_row = self.conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if card_row is None:
            return None
        card = row_to_dict(card_row)
        note = self.get_note(card["note_id"])
        if note:
            card["note"] = note
            card["note_type"] = note["note_type"]
        return card

    def list_notes(self, note_type: str | None = None, tag: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        where, params = self._build_note_filters(note_type=note_type, tag=tag, archived=None)
        rows = self.conn.execute(
            f"SELECT * FROM notes {where} ORDER BY updated_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [self._note_summary(row_to_dict(row)) for row in rows]

    def list_cards(
        self,
        note_type: str | None = None,
        state: str | None = None,
        due_only: bool = False,
        tag: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        now = to_utc_iso(utc_now())
        sql = """
            SELECT c.id, c.note_id, c.card_type, c.state, c.due_at, c.suspended, c.interval_days,
                   n.note_type, n.tags, n.is_archived
            FROM cards c
            JOIN notes n ON n.id = c.note_id
            WHERE c.suspended = 0 AND n.is_archived = 0
        """
        params: list[Any] = []
        if note_type:
            sql += " AND n.note_type = ?"
            params.append(note_type)
        if state:
            sql += " AND c.state = ?"
            params.append(state)
        if tag:
            sql += " AND (',' || n.tags || ',') LIKE ?"
            params.append(f"%,{normalize_tags(tag)},%")
        if due_only:
            sql += " AND (c.state = 'new' OR (c.due_at IS NOT NULL AND c.due_at <= ?))"
            params.append(now)
        sql += " ORDER BY CASE WHEN c.due_at IS NULL THEN 0 ELSE 1 END, c.due_at, c.id LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        results = [row_to_dict(row) for row in rows]
        for result in results:
            result["prompt_preview"] = self.prompt_preview(result["note_id"], result["card_type"])
        return results

    def get_review_cards(
        self,
        note_type: str | None = None,
        tag: str | None = None,
        limit: int | None = None,
        mode: str = "all",
    ) -> list[dict[str, Any]]:
        now = to_utc_iso(utc_now())
        sql = """
            SELECT c.id
            FROM cards c
            JOIN notes n ON n.id = c.note_id
            WHERE c.suspended = 0 AND n.is_archived = 0
        """
        params: list[Any] = []
        if note_type:
            sql += " AND n.note_type = ?"
            params.append(note_type)
        if tag:
            sql += " AND (',' || n.tags || ',') LIKE ?"
            params.append(f"%,{normalize_tags(tag)},%")
        if mode == "new":
            sql += " AND c.state = 'new'"
        elif mode == "due":
            sql += " AND c.state != 'new' AND c.due_at IS NOT NULL AND c.due_at <= ?"
            params.append(now)
        else:
            sql += " AND (c.state = 'new' OR (c.due_at IS NOT NULL AND c.due_at <= ?))"
            params.append(now)
        sql += " ORDER BY CASE WHEN c.due_at IS NULL THEN 0 ELSE 1 END, c.due_at, c.id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        ids = [row["id"] for row in self.conn.execute(sql, params).fetchall()]
        cards: list[dict[str, Any]] = []
        for card_id in ids:
            card = self.get_card(card_id)
            if card is not None:
                cards.append(card)
        return cards

    def apply_review(self, card_id: int, grade: str, schedule_result: Any) -> None:
        card = self.conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
        if card is None:
            raise ValueError(f"Card {card_id} not found")
        before = row_to_dict(card)
        self.conn.execute(
            """
            UPDATE cards
            SET state = ?, due_at = ?, interval_days = ?, ease_factor = ?, step_index = ?,
                lapses = lapses + ?, review_count = review_count + 1, last_reviewed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                schedule_result.state_after,
                schedule_result.due_after,
                schedule_result.interval_after,
                schedule_result.ease_after,
                schedule_result.step_index_after,
                schedule_result.lapses_delta,
                schedule_result.reviewed_at and schedule_result.reviewed_at.isoformat().replace("+00:00", "Z"),
                schedule_result.reviewed_at and schedule_result.reviewed_at.isoformat().replace("+00:00", "Z"),
                card_id,
            ),
        )
        self.conn.execute(
            """
            INSERT INTO reviews (
                card_id, reviewed_at, grade, state_before, state_after,
                interval_before, interval_after, ease_before, ease_after,
                due_before, due_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                card_id,
                schedule_result.reviewed_at.isoformat().replace("+00:00", "Z"),
                grade,
                before["state"],
                schedule_result.state_after,
                before["interval_days"],
                schedule_result.interval_after,
                before["ease_factor"],
                schedule_result.ease_after,
                before["due_at"],
                schedule_result.due_after,
            ),
        )
        self.conn.commit()

    def suspend_card(self, card_id: int, suspended: bool) -> None:
        self.conn.execute("UPDATE cards SET suspended = ?, updated_at = ? WHERE id = ?", (1 if suspended else 0, to_utc_iso(utc_now()), card_id))
        self.conn.commit()

    def archive_note(self, note_id: int, archived: bool) -> None:
        self.conn.execute("UPDATE notes SET is_archived = ?, updated_at = ? WHERE id = ?", (1 if archived else 0, to_utc_iso(utc_now()), note_id))
        self.conn.commit()

    def summary_stats(self) -> dict[str, Any]:
        today = to_utc_iso(utc_now())[:10]
        return {
            "notes": self.conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
            "active_notes": self.conn.execute("SELECT COUNT(*) FROM notes WHERE is_archived = 0").fetchone()[0],
            "cards": self.conn.execute("SELECT COUNT(*) FROM cards").fetchone()[0],
            "due_cards": self.conn.execute(
                "SELECT COUNT(*) FROM cards c JOIN notes n ON n.id = c.note_id WHERE c.suspended = 0 AND n.is_archived = 0 AND (c.state = 'new' OR (c.due_at IS NOT NULL AND c.due_at <= ?))",
                (to_utc_iso(utc_now()),),
            ).fetchone()[0],
            "reviews_today": self.conn.execute("SELECT COUNT(*) FROM reviews WHERE substr(reviewed_at, 1, 10) = ?", (today,)).fetchone()[0],
        }

    def note_stats(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT note_type, is_archived, COUNT(*) AS count
            FROM notes
            GROUP BY note_type, is_archived
            ORDER BY note_type, is_archived
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def card_stats(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT n.note_type, c.state, COUNT(*) AS count
            FROM cards c
            JOIN notes n ON n.id = c.note_id
            GROUP BY n.note_type, c.state
            ORDER BY n.note_type, c.state
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def daily_review_stats(self, days: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT substr(reviewed_at, 1, 10) AS day, COUNT(*) AS review_count
            FROM reviews
            WHERE reviewed_at >= datetime('now', ?)
            GROUP BY day
            ORDER BY day DESC
            """,
            (f"-{days} days",),
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def prompt_preview(self, note_id: int, card_type: str) -> str:
        note = self.get_note(note_id)
        if not note:
            return ""
        if card_type == "hanzi_to_meaning":
            return note["hanzi"]
        if card_type == "english_to_hanzi":
            return note["english"]
        if card_type == "char_to_meaning":
            return note["hanzi"]
        if card_type == "meaning_to_char":
            return note["english"]
        if card_type == "sentence_to_meaning":
            return note["sentence_cn"]
        if card_type == "cloze_focus_term":
            from sc.cardgen import build_cloze

            return build_cloze(note["sentence_cn"], note.get("focus_term", ""))
        return ""

    def _note_summary(self, note: dict[str, Any]) -> dict[str, Any]:
        detail = self.get_note(note["id"])
        summary = note.copy()
        if detail:
            summary.update({key: value for key, value in detail.items() if key not in {"cards"}})
        summary["prompt_preview"] = self._preview_for_note(summary)
        summary["card_count"] = self.conn.execute("SELECT COUNT(*) FROM cards WHERE note_id = ?", (note["id"],)).fetchone()[0]
        return summary

    def _preview_for_note(self, note: dict[str, Any]) -> str:
        if note["note_type"] in {"vocab", "char"}:
            return note.get("hanzi", "")
        return note.get("sentence_cn", "")

    def _build_note_filters(self, note_type: str | None, tag: str | None, archived: bool | None) -> tuple[str, list[Any]]:
        clauses = []
        params: list[Any] = []
        if note_type:
            validate_note_type(note_type)
            clauses.append("note_type = ?")
            params.append(note_type)
        if tag:
            clauses.append("(',' || tags || ',') LIKE ?")
            params.append(f"%,{normalize_tags(tag)},%")
        if archived is not None:
            clauses.append("is_archived = ?")
            params.append(1 if archived else 0)
        if not clauses:
            return "", params
        return "WHERE " + " AND ".join(clauses), params
