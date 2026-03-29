"""SQLite access for bundled `places_clean.db`."""

from __future__ import annotations

import sqlite3
from typing import List

from neptou_api.config import PLACES_DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(PLACES_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all_place_names() -> List[str]:
    try:
        conn = _connect()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM places ORDER BY name")
            return [row["name"] for row in cursor.fetchall()]
        finally:
            conn.close()
    except Exception:
        return []


def search_places_text(query: str, limit: int) -> List[sqlite3.Row]:
    try:
        conn = _connect()
        try:
            cursor = conn.cursor()
            q = f"%{query}%"
            cursor.execute(
                """
                SELECT name, description, geohash
                FROM places
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name
                LIMIT ?
                """,
                (q, q, limit),
            )
            return cursor.fetchall()
        finally:
            conn.close()
    except Exception:
        return []


def fetch_places_by_geohash_prefix(hash_prefix: str) -> List[sqlite3.Row]:
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, latitude, longitude, geohash
            FROM places
            WHERE geohash LIKE ?
            """,
            (f"{hash_prefix}%",),
        )
        return cursor.fetchall()
    finally:
        conn.close()
