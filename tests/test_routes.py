"""Route-level tests using FastAPI's TestClient.

``database.connect`` is monkeypatched to use a temporary database so the real
``data/page2card.db`` is never created or modified.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from page2card import database, main

from .conftest import load_fixture

TARGET_URL = "https://example.com/article"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_file = tmp_path / "routes.db"
    original_connect = database.connect

    def temp_connect(db_path=None):
        return original_connect(db_file)

    monkeypatch.setattr(main.database, "connect", temp_connect)
    return TestClient(main.app)


def test_index_empty(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "收藏一篇文章" in resp.text


@respx.mock
def test_capture_saves_and_redirects(client: TestClient):
    respx.get(TARGET_URL).mock(
        return_value=httpx.Response(200, html=load_fixture("article.html"))
    )
    resp = client.post(
        "/capture",
        data={"url": TARGET_URL, "category": "科技"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    detail = client.get(resp.headers["location"])
    assert "新一代 AI 模型" in detail.text
    assert "更有效率的訓練方法" in detail.text
    assert "科技" in detail.text


def test_capture_rejects_bad_url(client: TestClient):
    resp = client.post(
        "/capture",
        data={"url": "ftp://example.com", "category": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "http://" in resp.text


@respx.mock
def test_capture_shows_friendly_error_on_http_failure(client: TestClient):
    respx.get(TARGET_URL).mock(return_value=httpx.Response(500, text="boom"))
    resp = client.post(
        "/capture",
        data={"url": TARGET_URL, "category": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert "HTTP 500" in resp.text


@respx.mock
def test_category_filter(client: TestClient):
    respx.get(TARGET_URL).mock(
        return_value=httpx.Response(200, html=load_fixture("article.html"))
    )
    client.post("/capture", data={"url": TARGET_URL, "category": "科技"})

    listing = client.get("/?category=科技")
    assert "新一代 AI 模型" in listing.text
    empty = client.get("/?category=財經")
    assert "這個分類底下還沒有文章" in empty.text


@respx.mock
def test_delete_article(client: TestClient):
    respx.get(TARGET_URL).mock(
        return_value=httpx.Response(200, html=load_fixture("article.html"))
    )
    client.post("/capture", data={"url": TARGET_URL, "category": ""})

    resp = client.post("/articles/1/delete", follow_redirects=False)
    assert resp.status_code == 303
    assert client.get("/articles/1").status_code == 404


def test_detail_404_for_missing(client: TestClient):
    assert client.get("/articles/999").status_code == 404


@respx.mock
def test_captured_text_is_escaped_not_executed(client: TestClient):
    malicious = (
        "<!DOCTYPE html><html><head>"
        "<meta property='og:title' content='XSS 測試'></head>"
        "<body><article><p>before<script>alert(1)</script>after</p>"
        "<p>留下這段安全文字</p></article></body></html>"
    )
    respx.get(TARGET_URL).mock(return_value=httpx.Response(200, html=malicious))
    resp = client.post(
        "/capture", data={"url": TARGET_URL, "category": ""}, follow_redirects=False
    )
    detail = client.get(resp.headers["location"])
    # The script tag was stripped during extraction; nothing executable remains.
    assert "<script>alert(1)</script>" not in detail.text
    assert "留下這段安全文字" in detail.text
