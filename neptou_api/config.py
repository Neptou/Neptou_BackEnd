"""Paths and environment-backed settings."""

from __future__ import annotations

import os
from pathlib import Path

# Repo / deploy root (parent of `neptou_api/`)
ROOT_DIR = Path(__file__).resolve().parent.parent


def _places_db_path() -> Path:
    raw = os.environ.get("PLACES_DB_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return ROOT_DIR / "places_clean.db"


PLACES_DB_PATH: Path = _places_db_path()
