"""FastAPI application: routes, templates, and form handling.

The starter can capture a page (fetch + extract title/body), store it, list the
saved articles, filter by category, view one article, and delete it.

It deliberately does NOT generate AI summaries or share cards yet — that is the
next step, implemented via the Codex issue (see PAGE2CARD_ISSUE.md).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import database
from .repository import Repository
from .services.extractor import ExtractError, extract_content
from .services.fetcher import FetchError, fetch_page

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="page2card")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

CATEGORY_MAX = 50


def get_repository() -> Repository:
    """Open a fresh repository bound to a new connection."""
    return Repository(database.connect())


def validate_input(url: str, category: str) -> tuple[str, str | None, str | None]:
    """Validate the capture form. Returns ``(url, category_or_none, error)``."""
    url = url.strip()
    category = category.strip()

    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return url, category or None, "網址只接受 http:// 或 https:// 開頭。"

    if len(category) > CATEGORY_MAX:
        return url, category or None, f"分類最多 {CATEGORY_MAX} 個字元。"

    return url, (category or None), None


# --- Routes -------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def index(request: Request, category: str | None = None) -> HTMLResponse:
    repo = get_repository()
    try:
        articles = repo.list_articles(category=category)
        categories = repo.list_categories()
    finally:
        repo.conn.close()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "articles": articles,
            "categories": categories,
            "active_category": category,
            "error": None,
            "form": {"url": "", "category": ""},
        },
    )


@app.post("/capture", response_model=None)
async def capture(
    request: Request,
    url: str = Form(""),
    category: str = Form(""),
) -> HTMLResponse | RedirectResponse:
    clean_url, clean_category, error = validate_input(url, category)

    if error is None:
        try:
            html = await fetch_page(clean_url)
            title, content = extract_content(html)
        except (FetchError, ExtractError) as exc:
            error = str(exc)

    if error is None:
        repo = get_repository()
        try:
            article = repo.add_article(clean_url, title, content, clean_category)
        finally:
            repo.conn.close()
        return RedirectResponse(f"/articles/{article.id}", status_code=303)

    # Re-render the dashboard with the error and the user's input preserved.
    repo = get_repository()
    try:
        articles = repo.list_articles()
        categories = repo.list_categories()
    finally:
        repo.conn.close()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "articles": articles,
            "categories": categories,
            "active_category": None,
            "error": error,
            "form": {"url": url, "category": category},
        },
        status_code=400,
    )


@app.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int) -> HTMLResponse:
    repo = get_repository()
    try:
        article = repo.get_article(article_id)
    finally:
        repo.conn.close()

    if article is None:
        return templates.TemplateResponse(
            request, "not_found.html", {}, status_code=404
        )
    return templates.TemplateResponse(
        request, "article_detail.html", {"article": article}
    )


@app.post("/articles/{article_id}/delete")
def delete_article(article_id: int) -> RedirectResponse:
    repo = get_repository()
    try:
        repo.delete_article(article_id)
    finally:
        repo.conn.close()
    return RedirectResponse("/", status_code=303)
