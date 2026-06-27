"""SQLite connection and schema management.

The data directory is created automatically on first use. Timestamps are
stored as Taiwan-time (UTC+8) ``YYYY-MM-DD HH:MM:SS`` strings.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url          TEXT NOT NULL,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,
    category     TEXT,
    created_at   TEXT NOT NULL,
    published_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_articles_created
    ON articles(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_articles_category
    ON articles(category);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply lightweight, additive migrations to an existing database."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(articles)")}
    if "published_at" not in columns:
        conn.execute("ALTER TABLE articles ADD COLUMN published_at TEXT")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection, creating the parent directory and schema.

    ``data/`` is created with ``mkdir(parents=True, exist_ok=True)`` rather than
    committing an empty directory or a ``.gitkeep`` placeholder.
    """
    path = Path(db_path) if db_path is not None else config.DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
