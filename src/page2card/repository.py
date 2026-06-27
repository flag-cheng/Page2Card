"""Data access layer for captured articles."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .models import Article

# Taiwan time (UTC+8, no daylight saving). Timestamps are stored in this zone.
TAIPEI_TZ = timezone(timedelta(hours=8), name="Asia/Taipei")


def now_iso() -> str:
    """Return the current Taiwan time as an ISO-8601 string (no microseconds)."""
    return datetime.now(TAIPEI_TZ).replace(microsecond=0).isoformat()


def _row_to_article(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        content=row["content"],
        category=row["category"],
        created_at=row["created_at"],
    )


class Repository:
    """Thin wrapper around a SQLite connection providing typed operations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add_article(
        self, url: str, title: str, content: str, category: str | None
    ) -> Article:
        created_at = now_iso()
        cursor = self.conn.execute(
            """
            INSERT INTO articles (url, title, content, category, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (url, title, content, category, created_at),
        )
        self.conn.commit()
        return self.get_article(cursor.lastrowid)

    def get_article(self, article_id: int) -> Article | None:
        row = self.conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        return _row_to_article(row) if row else None

    def list_articles(self, category: str | None = None) -> list[Article]:
        """List articles, newest first, optionally filtered by category."""
        if category:
            rows = self.conn.execute(
                """
                SELECT * FROM articles
                WHERE category = ?
                ORDER BY created_at DESC, id DESC
                """,
                (category,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM articles ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [_row_to_article(r) for r in rows]

    def list_categories(self) -> list[str]:
        """Return the distinct, non-empty categories in use, alphabetically."""
        rows = self.conn.execute(
            """
            SELECT DISTINCT category FROM articles
            WHERE category IS NOT NULL AND category <> ''
            ORDER BY category
            """
        ).fetchall()
        return [row["category"] for row in rows]

    def delete_article(self, article_id: int) -> bool:
        """Delete an article. Returns True if a row was removed."""
        cursor = self.conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        self.conn.commit()
        return cursor.rowcount > 0
