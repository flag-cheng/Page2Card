"""Data access layer for captured articles."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

from .models import Article, ArticleSummary, CardImage

# Taiwan time (UTC+8, no daylight saving). Timestamps are stored in this zone.
TAIPEI_TZ = timezone(timedelta(hours=8), name="Asia/Taipei")


def now_iso() -> str:
    """Return the current Taiwan time as ``YYYY-MM-DD HH:MM:SS`` (no timezone)."""
    return datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _row_to_article(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        content=row["content"],
        category=row["category"],
        created_at=row["created_at"],
        published_at=row["published_at"],
    )


def _row_to_summary(row: sqlite3.Row) -> ArticleSummary:
    return ArticleSummary(
        article_id=row["article_id"],
        quote=row["quote"],
        overview=row["overview"],
        key_points=json.loads(row["key_points_json"]),
        input_truncated=bool(row["input_truncated"]),
        created_at=row["created_at"],
    )


def _row_to_card(row: sqlite3.Row) -> CardImage:
    return CardImage(
        article_id=row["article_id"],
        position=row["position"],
        role=row["role"],
        style_code=row["style_code"],
        size_code=row["size_code"],
        path=row["path"],
        mime_type=row["mime_type"],
        created_at=row["created_at"],
    )


class Repository:
    """Thin wrapper around a SQLite connection providing typed operations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def add_article(
        self,
        url: str,
        title: str,
        content: str,
        category: str | None,
        published_at: str | None = None,
    ) -> Article:
        created_at = now_iso()
        cursor = self.conn.execute(
            """
            INSERT INTO articles
                (url, title, content, category, created_at, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (url, title, content, category, created_at, published_at),
        )
        self.conn.commit()
        return self.get_article(cursor.lastrowid)

    def get_article(self, article_id: int) -> Article | None:
        row = self.conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        ).fetchone()
        if row is None:
            return None
        article = _row_to_article(row)
        article.summary = self.get_summary(article_id)
        article.card_images = self.list_card_images(article_id)
        return article

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

    def get_summary(self, article_id: int) -> ArticleSummary | None:
        row = self.conn.execute(
            "SELECT * FROM article_summaries WHERE article_id = ?", (article_id,)
        ).fetchone()
        return _row_to_summary(row) if row else None

    def save_summary(self, summary: ArticleSummary) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO article_summaries
                (
                    article_id, quote, overview, key_points_json,
                    input_truncated, created_at
                )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                summary.article_id,
                summary.quote,
                summary.overview,
                json.dumps(summary.key_points, ensure_ascii=False),
                int(summary.input_truncated),
                now_iso(),
            ),
        )
        self.conn.commit()

    def list_card_images(self, article_id: int) -> list[CardImage]:
        rows = self.conn.execute(
            "SELECT * FROM card_images WHERE article_id = ? ORDER BY position",
            (article_id,),
        ).fetchall()
        return [_row_to_card(row) for row in rows]

    def replace_card_images(self, article_id: int, cards: list[CardImage]) -> None:
        self.conn.execute("DELETE FROM card_images WHERE article_id = ?", (article_id,))
        for card in cards:
            self.conn.execute(
                """
                INSERT INTO card_images
                    (
                        article_id, position, role, style_code,
                        size_code, path, mime_type, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article_id,
                    card.position,
                    card.role,
                    card.style_code,
                    card.size_code,
                    card.path,
                    card.mime_type,
                    now_iso(),
                ),
            )
        self.conn.commit()

    def get_card_image(self, article_id: int, position: int) -> CardImage | None:
        row = self.conn.execute(
            "SELECT * FROM card_images WHERE article_id = ? AND position = ?",
            (article_id, position),
        ).fetchone()
        return _row_to_card(row) if row else None
