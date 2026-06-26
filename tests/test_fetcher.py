"""Tests for the HTTP fetcher using RESPX mocks."""

from __future__ import annotations

import httpx
import pytest
import respx

from page2card.services.fetcher import FetchError, fetch_page

from .conftest import load_fixture

URL = "https://example.com/article"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_returns_html_on_success():
    respx.get(URL).mock(
        return_value=httpx.Response(200, html=load_fixture("article.html"))
    )
    body = await fetch_page(URL)
    assert "新一代 AI 模型" in body


@pytest.mark.asyncio
@respx.mock
async def test_fetch_rejects_http_error():
    respx.get(URL).mock(return_value=httpx.Response(404, text="nope"))
    with pytest.raises(FetchError, match="404"):
        await fetch_page(URL)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_rejects_non_html():
    respx.get(URL).mock(
        return_value=httpx.Response(
            200, json={"x": 1}, headers={"content-type": "application/json"}
        )
    )
    with pytest.raises(FetchError, match="HTML"):
        await fetch_page(URL)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_handles_timeout():
    respx.get(URL).mock(side_effect=httpx.ConnectTimeout("boom"))
    with pytest.raises(FetchError, match="逾時"):
        await fetch_page(URL)
