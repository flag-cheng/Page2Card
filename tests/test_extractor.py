"""Tests for title/body extraction."""

from __future__ import annotations

import pytest
from bs4 import BeautifulSoup

from page2card.services.extractor import ExtractError, extract_content, extract_title

from .conftest import load_fixture


def test_extract_prefers_og_title():
    title, _ = extract_content(load_fixture("article.html"))
    assert title == "新一代 AI 模型發表，效能大幅提升"


def test_body_keeps_article_text_and_drops_chrome():
    _, body = extract_content(load_fixture("article.html"))
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
