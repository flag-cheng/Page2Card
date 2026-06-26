"""Domain models for page2card."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Article:
    """A captured web article.

    The starter stores the page title, normalized body text, an optional
    category/topic label, and timestamps. AI summaries and share cards are NOT
    part of the starter — they are added later via the Codex issue.
    """

    id: int
    url: str
    title: str
    content: str
    category: str | None
    created_at: str

    @property
    def excerpt(self) -> str:
        """A short preview of the body for list views."""
        text = self.content.strip()
        return text[:140] + "…" if len(text) > 140 else text
