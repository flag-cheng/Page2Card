"""Server-side fetching of article pages with sensible limits.

All errors are surfaced as :class:`FetchError` with a user-friendly message;
internal details (stack traces, paths) are never exposed to the UI.
"""

from __future__ import annotations

import httpx

from .. import config


class FetchError(Exception):
    """Raised when a page cannot be fetched or is not usable HTML."""


def _is_html(content_type: str) -> bool:
    main = content_type.split(";", 1)[0].strip().lower()
    return main in {"text/html", "application/xhtml+xml"}


async def fetch_page(url: str) -> str:
    """Fetch ``url`` and return the decoded HTML body.

    Raises :class:`FetchError` for invalid URLs, connection/DNS errors, timeouts,
    HTTP 4xx/5xx, non-HTML responses, or oversized bodies.
    """
    timeout = httpx.Timeout(
        connect=config.CONNECT_TIMEOUT,
        read=config.READ_TIMEOUT,
        write=config.READ_TIMEOUT,
        pool=config.CONNECT_TIMEOUT,
    )
    headers = {"User-Agent": config.USER_AGENT}

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            response = await client.get(url)
    except httpx.TimeoutException as exc:
        raise FetchError("連線逾時，請稍後再試。") from exc
    except httpx.ConnectError as exc:
        raise FetchError("無法連線到該網址，請確認網址是否正確。") from exc
    except httpx.InvalidURL as exc:
        raise FetchError("網址格式錯誤。") from exc
    except httpx.RequestError as exc:
        raise FetchError("取得網頁時發生網路錯誤。") from exc

    if response.status_code >= 400:
        raise FetchError(f"網頁回應錯誤（HTTP {response.status_code}）。")

    content_type = response.headers.get("content-type", "")
    if not _is_html(content_type):
        raise FetchError("此網址未回傳 HTML 內容。")

    if len(response.content) > config.MAX_RESPONSE_BYTES:
        raise FetchError("網頁內容過大，超過處理上限。")

    return response.text
