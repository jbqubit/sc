from __future__ import annotations

import os
from pathlib import Path


APP_DIR = Path.home() / ".local" / "share" / "sc"
DEFAULT_DB_NAME = "sc.db"


def default_db_path() -> Path:
    env_path = os.environ.get("SC_DB_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return (APP_DIR / DEFAULT_DB_NAME).resolve()


def resolve_db_path(explicit: str | Path | None) -> Path:
    if explicit is None:
        return default_db_path()
    return Path(explicit).expanduser().resolve()
