# /srv/dj-stream/app/db.py
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from app.config import DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER,
            vote TEXT NOT NULL CHECK(vote IN ('up','down','more_energy','less_energy')),
            energy_at_vote INTEGER NOT NULL,
            genre_at_vote TEXT,
            track_path TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tracks (
            path TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            album TEXT,
            bpm REAL,
            musical_key TEXT,
            camelot TEXT,
            loudness_lufs REAL,
            energy INTEGER,
            energy_confidence REAL,
            mood TEXT,
            genre TEXT,
            analyzed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS missions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            target INTEGER NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            reward TEXT,
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_votes_user ON votes(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_votes_created ON votes(created_at);
        """)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(str(DB_PATH), timeout=30)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def get_state(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_conn() as con:
        row = con.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def set_state(key: str, value: str) -> None:
    with get_conn() as con:
        con.execute(
            "INSERT INTO app_state(key, value, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, utc_now()),
        )


def get_energy() -> int:
    return int(get_state("energy", "7") or "7")


def set_energy(n: int) -> None:
    if not 1 <= n <= 10:
        raise ValueError("energy must be 1-10")
    set_state("energy", str(n))


def get_genre() -> str:
    return get_state("genre", "psytrance") or "psytrance"


def set_genre(g: str) -> None:
    set_state("genre", g)


def record_vote(user_id: int, chat_id: Optional[int], vote: str,
                energy: int, genre: str, track_path: Optional[str] = None) -> None:
    with get_conn() as con:
        con.execute(
            "INSERT INTO votes(user_id, chat_id, vote, energy_at_vote, genre_at_vote, track_path, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user_id, chat_id, vote, energy, genre, track_path, utc_now()),
        )


def recent_votes(limit: int = 50) -> list[sqlite3.Row]:
    with get_conn() as con:
        return list(con.execute(
            "SELECT * FROM votes ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall())
