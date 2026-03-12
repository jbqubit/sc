from __future__ import annotations

from typing import Iterable

from src.models import NOTE_TYPES


REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "vocab": ("hanzi", "pinyin", "english"),
    "char": ("hanzi", "english"),
    "sentence": ("sentence_cn", "sentence_en"),
}

OPTIONAL_COLUMNS: dict[str, tuple[str, ...]] = {
    "vocab": ("example_cn", "example_en", "tags", "source"),
    "char": ("pinyin", "components", "mnemonic", "example_cn", "example_en", "tags", "source"),
    "sentence": ("sentence_pinyin", "focus_term", "notes", "tags", "source"),
}


def validate_note_type(note_type: str) -> None:
    if note_type not in NOTE_TYPES:
        raise ValueError(f"Unsupported note type: {note_type}")


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def normalize_tags(value: str | None) -> str:
    tags = [part.strip() for part in (value or "").split(",") if part.strip()]
    return ",".join(tags)


def validate_payload(note_type: str, payload: dict[str, str]) -> dict[str, str]:
    validate_note_type(note_type)
    cleaned = {key: normalize_text(value) for key, value in payload.items()}
    cleaned["tags"] = normalize_tags(cleaned.get("tags", ""))
    cleaned["source"] = normalize_text(cleaned.get("source", ""))
    for column in REQUIRED_COLUMNS[note_type]:
        if not cleaned.get(column):
            raise ValueError(f"{note_type} field '{column}' is required")
    if note_type == "sentence":
        focus_term = cleaned.get("focus_term", "")
        sentence = cleaned.get("sentence_cn", "")
        if focus_term and focus_term not in sentence:
            raise ValueError("sentence field 'focus_term' must appear in sentence_cn")
    return cleaned


def validate_import_columns(note_type: str, columns: Iterable[str]) -> None:
    validate_note_type(note_type)
    missing = [column for column in REQUIRED_COLUMNS[note_type] if column not in columns]
    if missing:
        raise ValueError(f"Missing required columns for {note_type}: {', '.join(missing)}")
