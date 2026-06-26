"""Extract a title and readable body text from raw HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .. import config

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


def extract_content(html: str) -> tuple[str, str]:
    """Return ``(title, body_text)`` extracted and normalized from ``html``.

    Removes non-content elements, prefers the ``<article>``/``<main>`` region if
    present, collapses whitespace, and truncates to ``MAX_CONTENT_CHARS``.
    Raises :class:`ExtractError` when the body is empty.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)

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

    return title, text
