from __future__ import annotations

import csv
from pathlib import Path

from sc.models import ImportResult
from sc.repository import Repository
from sc.validators import OPTIONAL_COLUMNS, REQUIRED_COLUMNS, normalize_text, validate_import_columns


def import_csv(repo: Repository, note_type: str, path: str | Path, delimiter: str = ",") -> ImportResult:
    result = ImportResult()
    csv_path = Path(path)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")
        validate_import_columns(note_type, reader.fieldnames)
        allowed_columns = set(REQUIRED_COLUMNS[note_type] + OPTIONAL_COLUMNS[note_type])
        for index, row in enumerate(reader, start=2):
            payload = {column: normalize_text(row.get(column, "")) for column in allowed_columns}
            try:
                repo.create_note(note_type, payload)
                result.accepted += 1
            except Exception as exc:
                result.rejected += 1
                result.errors.append(f"row {index}: {exc}")
    return result
