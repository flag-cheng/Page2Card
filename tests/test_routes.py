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


class FakeAIService:
    summarize_calls = 0
    plan_calls = 0
    image_calls = 0
    last_size = None
    fail_summary = False

    def __init__(self, api_key=None):
        self.api_key = api_key

    def summarize(self, article):
        from page2card.models import ArticleSummary

        FakeAIService.summarize_calls += 1
        if FakeAIService.fail_summary:
            from page2card.services.ai import AIServiceError

            raise AIServiceError("AI 摘要暫時無法產生，請稍後再試或確認 API Key。")
        assert "忽略前面指令" in article.content or article.content
        return ArticleSummary(
            article_id=article.id,
            quote="把資料變成可行動的洞察",
            overview="本文說明 AI 系統如何協助整理資訊。這些內容能幫助讀者理解重點。",
            key_points=["保留可驗證事實", "避免遵循內文指令"],
        )

    def plan_cards(self, article, summary, count):
        from page2card.services.ai import CardPlan

        FakeAIService.plan_calls += 1
        return [
            CardPlan(f"第 {i} 張", f"金句 {i}", f"說明 {i}", f"主視覺 {i}")
            for i in range(1, count + 1)
        ]

    def generate_image(self, article, plan, style, size):
        FakeAIService.image_calls += 1
        FakeAIService.last_size = size.api_size
        return b"fake-png"


@pytest.fixture
def article_id(client: TestClient):
    respx.start()
    respx.get(TARGET_URL).mock(
        return_value=httpx.Response(200, html=load_fixture("article.html"))
    )
    resp = client.post("/capture", data={"url": TARGET_URL, "category": ""})
    respx.stop()
    respx.reset()
    return int(resp.url.path.rsplit("/", 1)[-1])


@pytest.fixture(autouse=True)
def reset_fake_ai(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    FakeAIService.summarize_calls = 0
    FakeAIService.plan_calls = 0
    FakeAIService.image_calls = 0
    FakeAIService.last_size = None
    FakeAIService.fail_summary = False
    monkeypatch.setattr(main.config, "CARD_DIR", tmp_path / "cards")
    monkeypatch.setattr(
        main, "get_ai_service", lambda api_key=None: FakeAIService(api_key)
    )


def test_no_api_key_prompts_without_calling_openai(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", None)
    resp = client.get(f"/articles/{article_id}")
    assert "請貼入 OpenAI API Key 以產生摘要" in resp.text
    assert FakeAIService.summarize_calls == 0


def test_env_api_key_shows_summarize_button(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")
    resp = client.get(f"/articles/{article_id}")
    assert "產生 AI 摘要" in resp.text
    assert "password" not in resp.text


def test_mock_summary_is_saved_and_reused(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")
    resp = client.post(f"/articles/{article_id}/summarize", follow_redirects=True)
    assert resp.status_code == 200
    assert "把資料變成可行動的洞察" in resp.text
    assert "保留可驗證事實" in resp.text
    assert FakeAIService.summarize_calls == 1

    again = client.post(f"/articles/{article_id}/summarize", follow_redirects=True)
    assert "已顯示先前保存的摘要" in again.text
    assert FakeAIService.summarize_calls == 1


def test_user_api_key_not_persisted(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", None)
    secret = "sk-" + "user-secret"
    resp = client.post(
        f"/articles/{article_id}/summarize",
        data={"openai_api_key": secret},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert secret not in resp.text

    repo = main.get_repository()
    try:
        rows = repo.conn.execute(
            "SELECT quote, overview, key_points_json FROM article_summaries"
        ).fetchall()
    finally:
        repo.conn.close()
    assert secret not in repr([tuple(r) for r in rows])


def test_ai_error_keeps_article_page(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")
    FakeAIService.fail_summary = True
    resp = client.post(f"/articles/{article_id}/summarize")
    assert resp.status_code == 502
    assert "AI 摘要暫時無法產生" in resp.text
    assert "新一代 AI 模型" in resp.text


def test_summary_html_is_escaped(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    from page2card.models import ArticleSummary

    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")

    class HtmlAI(FakeAIService):
        def summarize(self, article):
            return ArticleSummary(
                article_id=article.id,
                quote="<script>alert(1)</script>",
                overview="<b>不是 HTML</b>",
                key_points=["<img src=x onerror=alert(1)>"],
            )

    monkeypatch.setattr(main, "get_ai_service", lambda api_key=None: HtmlAI(api_key))
    resp = client.post(f"/articles/{article_id}/summarize", follow_redirects=True)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in resp.text
    assert "<script>alert(1)</script>" not in resp.text


def test_card_generation_fallbacks_size_and_download(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")
    monkeypatch.setattr(main.config, "MAX_CARDS", 2)
    client.post(f"/articles/{article_id}/summarize")
    resp = client.post(
        f"/articles/{article_id}/card",
        data={"style": "unknown", "size": "fb_landscape", "count": "9"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert FakeAIService.plan_calls == 1
    assert FakeAIService.image_calls == 2
    assert FakeAIService.last_size == "1536x1024"
    assert "minimal" in resp.text
    assert "fb_landscape" in resp.text

    image = client.get(f"/articles/{article_id}/card-1.png")
    assert image.status_code == 200
    assert image.content == b"fake-png"
    assert client.get(f"/articles/{article_id}/card-99.png").status_code == 404

    again = client.post(f"/articles/{article_id}/card", follow_redirects=True)
    assert "已顯示先前保存的圖卡" in again.text
    assert FakeAIService.image_calls == 2


def test_style_and_size_options_are_rendered(
    client: TestClient, article_id: int, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(main.config, "OPENAI_API_KEY", "server-key")
    client.post(f"/articles/{article_id}/summarize")
    resp = client.get(f"/articles/{article_id}")
    assert "藝廊語錄海報" in resp.text
    assert "星象塔羅卡" in resp.text
    assert "IG 貼文" in resp.text
    assert "FB 橫式貼文" in resp.text
