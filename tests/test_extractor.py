"""Tests for title/body extraction."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from page2card.services.extractor import (
    ExtractError,
    extract_content,
    extract_published_at,
    extract_title,
)

from .conftest import load_fixture


def test_extract_prefers_og_title():
    title, _, _ = extract_content(load_fixture("article.html"))
    assert title == "新一代 AI 模型發表，效能大幅提升"


def test_body_keeps_article_text_and_drops_chrome():
    _, body, _ = extract_content(load_fixture("article.html"))
    assert "更有效率的訓練方法" in body
    # Navigation, ads, footer, scripts, styles are stripped.
    assert "首頁 新聞 關於我們" not in body
    assert "立即購買" not in body
    assert "版權所有" not in body
    assert "tracker should be removed" not in body


def test_title_falls_back_to_h1_then_title():
    soup = BeautifulSoup("<html><body><h1>只有 H1</h1></body></html>", "html.parser")
    assert extract_title(soup) == "只有 H1"

    soup2 = BeautifulSoup(
        "<html><head><title>只有 Title</title></head><body></body></html>",
        "html.parser",
    )
    assert extract_title(soup2) == "只有 Title"


def test_empty_html_raises():
    with pytest.raises(ExtractError):
        extract_content("<html><body></body></html>")


def test_published_at_from_meta_tag():
    soup = BeautifulSoup(
        "<html><head>"
        '<meta property="article:published_time" content="2026-06-25T08:30:00+08:00">'
        "</head><body><p>x</p></body></html>",
        "html.parser",
    )
    assert extract_published_at(soup) == "2026-06-25 08:30:00"


def test_published_at_converts_utc_to_taiwan():
    soup = BeautifulSoup(
        "<html><head>"
        '<meta property="article:published_time" content="2026-06-25T00:30:00Z">'
        "</head><body><p>x</p></body></html>",
        "html.parser",
    )
    # 00:30 UTC -> 08:30 Taiwan.
    assert extract_published_at(soup) == "2026-06-25 08:30:00"


def test_published_at_from_time_element():
    soup = BeautifulSoup(
        '<html><body><time datetime="2026-06-24T12:00:00+08:00">昨天</time>'
        "<p>x</p></body></html>",
        "html.parser",
    )
    assert extract_published_at(soup) == "2026-06-24 12:00:00"


def test_published_at_from_jsonld():
    soup = BeautifulSoup(
        '<html><head><script type="application/ld+json">'
        '{"@type": "NewsArticle", "datePublished": "2026-06-20T09:15:00+08:00"}'
        "</script></head><body><p>x</p></body></html>",
        "html.parser",
    )
    assert extract_published_at(soup) == "2026-06-20 09:15:00"


def test_published_at_absent_returns_none():
    soup = BeautifulSoup("<html><body><p>x</p></body></html>", "html.parser")
    assert extract_published_at(soup) is None


def test_published_at_unparseable_returns_none():
    soup = BeautifulSoup(
        "<html><head>"
        '<meta property="article:published_time" content="not a date">'
        "</head><body><p>x</p></body></html>",
        "html.parser",
    )
    assert extract_published_at(soup) is None
