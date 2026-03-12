from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from sc.cli import app


runner = CliRunner()


def test_cli_import_list_and_stats(tmp_path: Path):
    db_path = tmp_path / "cli.db"
    csv_path = tmp_path / "sentence.csv"
    csv_path.write_text(
        "sentence_cn,sentence_pinyin,sentence_en,focus_term,notes,tags,source\n"
        "我昨天去了学校。,wo3 zuo2 tian1 qu4 le xue2 xiao4.,I went to school yesterday.,学校,,hsk1,synthetic\n"
        "今天下雨了。,jin1 tian1 xia4 yu3 le.,It rained today.,,,weather,synthetic\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", "--db", str(db_path)])
    assert result.exit_code == 0

    result = runner.invoke(app, ["import", "sentence", str(csv_path), "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Imported 2 row(s)" in result.stdout

    result = runner.invoke(app, ["list", "notes", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "今天下雨了" in result.stdout

    result = runner.invoke(app, ["show", "note", "1", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "sentence" in result.stdout

    result = runner.invoke(app, ["suspend", "card", "1", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Suspended card 1" in result.stdout

    result = runner.invoke(app, ["archive", "note", "1", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Archived note 1" in result.stdout

    result = runner.invoke(app, ["stats", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Due Cards" in result.stdout
