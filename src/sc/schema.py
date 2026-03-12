from __future__ import annotations

import sqlite3


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY,
    note_type TEXT NOT NULL CHECK (note_type IN ('vocab', 'char', 'sentence')),
    tags TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    is_archived INTEGER NOT NULL DEFAULT 0 CHECK (is_archived IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vocab_notes (
    note_id INTEGER PRIMARY KEY,
    hanzi TEXT NOT NULL,
    pinyin TEXT NOT NULL,
    english TEXT NOT NULL,
    example_cn TEXT NOT NULL DEFAULT '',
    example_en TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS char_notes (
    note_id INTEGER PRIMARY KEY,
    hanzi TEXT NOT NULL,
    pinyin TEXT NOT NULL DEFAULT '',
    english TEXT NOT NULL,
    components TEXT NOT NULL DEFAULT '',
    mnemonic TEXT NOT NULL DEFAULT '',
    example_cn TEXT NOT NULL DEFAULT '',
    example_en TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sentence_notes (
    note_id INTEGER PRIMARY KEY,
    sentence_cn TEXT NOT NULL,
    sentence_pinyin TEXT NOT NULL DEFAULT '',
    sentence_en TEXT NOT NULL,
    focus_term TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL,
    card_type TEXT NOT NULL,
    prompt_lang TEXT NOT NULL DEFAULT '',
    answer_lang TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL CHECK (state IN ('new', 'learning', 'review', 'relearning')),
    due_at TEXT,
    step_index INTEGER NOT NULL DEFAULT 0,
    interval_days REAL NOT NULL DEFAULT 0,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    lapses INTEGER NOT NULL DEFAULT 0,
    review_count INTEGER NOT NULL DEFAULT 0,
    suspended INTEGER NOT NULL DEFAULT 0 CHECK (suspended IN (0, 1)),
    last_reviewed_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    UNIQUE (note_id, card_type)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    reviewed_at TEXT NOT NULL,
    grade TEXT NOT NULL CHECK (grade IN ('again', 'hard', 'good', 'easy')),
    state_before TEXT NOT NULL,
    state_after TEXT NOT NULL,
    interval_before REAL NOT NULL,
    interval_after REAL NOT NULL,
    ease_before REAL NOT NULL,
    ease_after REAL NOT NULL,
    due_before TEXT,
    due_after TEXT,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type);
CREATE INDEX IF NOT EXISTS idx_cards_due ON cards(due_at);
CREATE INDEX IF NOT EXISTS idx_cards_state_due ON cards(state, due_at);
CREATE INDEX IF NOT EXISTS idx_cards_note_id ON cards(note_id);
CREATE INDEX IF NOT EXISTS idx_reviews_card_id ON reviews(card_id);
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()
