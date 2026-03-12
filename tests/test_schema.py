from __future__ import annotations

from sc.db import connect


def test_schema_bootstraps_tables(tmp_path):
    conn = connect(tmp_path / "schema.db")
    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"notes", "vocab_notes", "char_notes", "sentence_notes", "cards", "reviews"} <= names
