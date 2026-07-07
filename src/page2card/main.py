"""FastAPI application: routes, templates, and form handling."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, database
from .repository import Repository
from .services.ai import AIService, AIServiceError, card_image_from_bytes
from .services.extractor import ExtractError, extract_content
from .services.fetcher import FetchError, fetch_page
from .styles import CARD_SIZES, CARD_STYLES, get_size, get_style

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


def get_ai_service(api_key: str | None = None) -> AIService:
    return AIService(api_key=api_key)


def ai_key_available() -> bool:
    return bool(config.OPENAI_API_KEY)


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


def _render_article(
    request: Request,
    article_id: int,
    status_code: int = 200,
    message: str | None = None,
    error: str | None = None,
) -> HTMLResponse:
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
        request,
        "article_detail.html",
        {
            "article": article,
            "card_styles": CARD_STYLES.values(),
            "card_sizes": CARD_SIZES.values(),
            "max_cards": config.MAX_CARDS,
            "default_style": (
                article.card_images[0].style_code if article.card_images else "minimal"
            ),
            "default_size": (
                article.card_images[0].size_code if article.card_images else "ig_post"
            ),
            "ai_key_available": ai_key_available(),
            "message": message,
            "error": error,
        },
        status_code=status_code,
    )


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
    request: Request, url: str = Form(""), category: str = Form("")
) -> HTMLResponse | RedirectResponse:
    clean_url, clean_category, error = validate_input(url, category)
    if error is None:
        try:
            html = await fetch_page(clean_url)
            title, content, published_at = extract_content(html)
        except (FetchError, ExtractError) as exc:
            error = str(exc)
    if error is None:
        repo = get_repository()
        try:
            article = repo.add_article(
                clean_url, title, content, clean_category, published_at
            )
        finally:
            repo.conn.close()
        return RedirectResponse(f"/articles/{article.id}", status_code=303)
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
    return _render_article(request, article_id)


@app.post("/articles/{article_id}/summarize", response_class=HTMLResponse)
def summarize_article(
    request: Request, article_id: int, openai_api_key: str = Form("")
) -> HTMLResponse:
    repo = get_repository()
    try:
        article = repo.get_article(article_id)
        if article is None:
            return templates.TemplateResponse(
                request, "not_found.html", {}, status_code=404
            )
        if len(article.content.strip()) < config.MIN_SUMMARY_CHARS:
            return _render_article(
                request, article_id, status_code=400, error="內容不足以產生摘要。"
            )
        if article.summary is not None:
            return _render_article(
                request, article_id, message="已顯示先前保存的摘要，未重複呼叫 AI。"
            )
        api_key = None if ai_key_available() else openai_api_key.strip()
        if not ai_key_available() and not api_key:
            return _render_article(
                request,
                article_id,
                status_code=400,
                error="請貼入 OpenAI API Key 以產生摘要。",
            )
        summary = get_ai_service(api_key).summarize(article)
        repo.save_summary(summary)
    except AIServiceError as exc:
        return _render_article(request, article_id, status_code=502, error=str(exc))
    finally:
        repo.conn.close()
    return RedirectResponse(f"/articles/{article_id}", status_code=303)


@app.post(
    "/articles/{article_id}/card", response_class=HTMLResponse, response_model=None
)
def generate_card(
    request: Request,
    article_id: int,
    style: str = Form("minimal"),
    size: str = Form("ig_post"),
    count: int = Form(1),
    openai_api_key: str = Form(""),
) -> HTMLResponse | RedirectResponse:
    style_obj = get_style(style)
    size_obj = get_size(size)
    count = max(1, min(config.MAX_CARDS, count))
    repo = get_repository()
    try:
        article = repo.get_article(article_id)
        if article is None:
            return templates.TemplateResponse(
                request, "not_found.html", {}, status_code=404
            )
        if article.summary is None:
            return _render_article(
                request,
                article_id,
                status_code=400,
                error="請先產生文字摘要，再產生圖卡。",
            )
        if article.card_images:
            return _render_article(
                request, article_id, message="已顯示先前保存的圖卡，未重複呼叫 AI。"
            )
        api_key = None if ai_key_available() else openai_api_key.strip()
        if not ai_key_available() and not api_key:
            return _render_article(
                request,
                article_id,
                status_code=400,
                error="請貼入 OpenAI API Key 以產生圖卡。",
            )
        service = get_ai_service(api_key)
        plans = service.plan_cards(article, article.summary, count)
        cards = []
        for position, plan in enumerate(plans, start=1):
            image = service.generate_image(article, plan, style_obj, size_obj)
            path = config.card_path(article_id, position)
            path.write_bytes(image)
            cards.append(
                card_image_from_bytes(
                    article_id, position, plan, style_obj, size_obj, image
                )
            )
        repo.replace_card_images(article_id, cards)
    except AIServiceError as exc:
        return _render_article(request, article_id, status_code=502, error=str(exc))
    finally:
        repo.conn.close()
    return RedirectResponse(f"/articles/{article_id}", status_code=303)


@app.get("/articles/{article_id}/card-{position}.png", response_model=None)
def download_card(article_id: int, position: int) -> FileResponse | HTMLResponse:
    repo = get_repository()
    try:
        card = repo.get_card_image(article_id, position)
    finally:
        repo.conn.close()
    path = config.card_path(article_id, position)
    if card is None or not path.exists() or path.name != card.path:
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(path, media_type=card.mime_type, filename=path.name)


@app.post("/articles/{article_id}/delete")
def delete_article(article_id: int) -> RedirectResponse:
    repo = get_repository()
    try:
        repo.delete_article(article_id)
    finally:
        repo.conn.close()
    return RedirectResponse("/", status_code=303)
