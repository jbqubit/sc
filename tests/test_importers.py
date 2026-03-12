from __future__ import annotations

from pathlib import Path

from sc.db import connect
from sc.importers import import_csv
from sc.repository import Repository


def test_import_csv_accepts_valid_and_rejects_invalid_rows(tmp_path: Path):
    csv_path = tmp_path / "vocab.csv"
    csv_path.write_text(
        "hanzi,pinyin,english,example_cn,example_en,tags,source\n"
        "学校,xue2 xiao4,school,我去学校,I go to school,hsk1,manual\n"
        ",ni3 hao3,hello,,,greeting,manual\n",
        encoding="utf-8",
    )
    repo = Repository(connect(tmp_path / "import.db"))
    result = import_csv(repo, "vocab", csv_path)
    assert result.accepted == 1
    assert result.rejected == 1
    assert result.errors
    assert repo.summary_stats()["notes"] == 1
