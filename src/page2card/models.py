"""Domain models for page2card."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ArticleSummary:
    article_id: int
    quote: str
    overview: str
    key_points: list[str] = field(default_factory=list)
    input_truncated: bool = False
    created_at: str | None = None


@dataclass(slots=True)
class CardImage:
    article_id: int
    position: int
    role: str
    style_code: str
    size_code: str
    path: str
    mime_type: str = "image/png"
    created_at: str | None = None


@dataclass(slots=True)
class Article:
    """A captured web article."""

    id: int
    url: str
    title: str
    content: str
    category: str | None
    created_at: str
    published_at: str | None = None
    summary: ArticleSummary | None = None
    card_images: list[CardImage] = field(default_factory=list)

    @property
    def excerpt(self) -> str:
        """A short preview of the body for list views."""
        text = self.content.strip()
        return text[:140] + "…" if len(text) > 140 else text
