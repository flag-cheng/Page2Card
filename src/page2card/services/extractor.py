"""Extract a title and readable body text from raw HTML."""

from __future__ import annotations

import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from .. import config
from ..repository import TAIPEI_TZ

# Elements whose content is not article text and should be removed entirely.
_NON_CONTENT_TAGS = (
    "script",
    "style",
    "noscript",
    "template",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
)

_WHITESPACE_RE = re.compile(r"[ \t ]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


class ExtractError(Exception):
    """Raised when no usable article content can be extracted."""


def extract_title(soup: BeautifulSoup) -> str:
    """Pick the best available title: og:title, <h1>, then <title>."""
    og = soup.find("meta", property="og:title")
    if og and og.get("content", "").strip():
        return og["content"].strip()

    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)

    return "（無標題）"


def _normalize_datetime(raw: str) -> str | None:
    """Parse an ISO-8601-ish datetime string and format it for display.

    Returns ``"YYYY-MM-DD HH:MM:SS"`` in Taiwan time, or ``None`` if the value
    cannot be parsed. Timezone-aware inputs are converted to UTC+8; naive inputs
    are assumed to already be local.
    """
    raw = raw.strip()
    if not raw:
        return None
    # ``fromisoformat`` accepts a trailing "Z" only on Python 3.11+, but to be
    # safe we normalize it to an explicit offset first.
    candidate = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(TAIPEI_TZ)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _published_from_jsonld(soup: BeautifulSoup) -> str | None:
    """Look for ``datePublished`` inside any ``application/ld+json`` block."""
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.string or script.get_text()
        if not text:
            continue
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            continue
        # JSON-LD may be a single object, a list, or wrapped in "@graph".
        candidates = data if isinstance(data, list) else [data]
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            graph = entry.get("@graph")
            nodes = graph if isinstance(graph, list) else [entry]
            for node in nodes:
                if isinstance(node, dict) and node.get("datePublished"):
                    return str(node["datePublished"])
    return None


def extract_published_at(soup: BeautifulSoup) -> str | None:
    """Best-effort extraction of the article's publish time, newest source first.

    Tries, in order: ``og:article:published_time`` / ``article:published_time``
    meta tags, a generic ``datePublished``/``publish-date`` meta, a ``<time>``
    element's ``datetime`` attribute, then JSON-LD ``datePublished``. Returns a
    display-ready Taiwan-time string, or ``None`` when nothing usable is found.
    """
    meta_keys = (
        ("property", "article:published_time"),
        ("property", "og:article:published_time"),
        ("name", "article:published_time"),
        ("name", "datePublished"),
        ("itemprop", "datePublished"),
        ("name", "publish-date"),
        ("name", "pubdate"),
    )
    for attr, value in meta_keys:
        tag = soup.find("meta", attrs={attr: value})
        if tag and tag.get("content"):
            normalized = _normalize_datetime(tag["content"])
            if normalized:
                return normalized

    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        normalized = _normalize_datetime(time_tag["datetime"])
        if normalized:
            return normalized

    jsonld = _published_from_jsonld(soup)
    if jsonld:
        normalized = _normalize_datetime(jsonld)
        if normalized:
            return normalized

    return None


def extract_content(html: str) -> tuple[str, str, str | None]:
    """Return ``(title, body_text, published_at)`` extracted from ``html``.

    Removes non-content elements, prefers the ``<article>``/``<main>`` region if
    present, collapses whitespace, and truncates to ``MAX_CONTENT_CHARS``.
    ``published_at`` is the article's publish time (Taiwan time) or ``None``.
    Raises :class:`ExtractError` when the body is empty.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    published_at = extract_published_at(soup)

    for tag in soup(_NON_CONTENT_TAGS):
        tag.decompose()

    # Prefer the main article region when the page marks one.
    region = soup.find("article") or soup.find("main") or soup.body or soup
    text = region.get_text(separator="\n")

    # Collapse intra-line whitespace, then trim each line and squeeze blanks.
    text = _WHITESPACE_RE.sub(" ", text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = _BLANKLINES_RE.sub("\n\n", text).strip()

    if not text:
        raise ExtractError("網頁沒有可擷取的文字內容。")

    if len(text) > config.MAX_CONTENT_CHARS:
        text = text[: config.MAX_CONTENT_CHARS].rstrip() + "…"

    return title, text, published_at
