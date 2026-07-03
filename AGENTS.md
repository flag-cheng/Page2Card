# AGENTS.md

## Project Overview

page2card is a single-user FastAPI article collector. Users paste an article URL, the backend fetches static HTML, extracts the title and readable content, stores it in SQLite, and lets users organize saved articles by category/topic.

The starter app intentionally stops at fetch, display, save, categorize, view, and delete. The current Cloud task work is tracked by GitHub Issue #4 and `PAGE2CARD_ISSUE.md`: add AI Traditional Chinese summaries and shareable card images.

## Environment Setup

Use Python 3.12+ and `uv`.

```bash
uv sync --frozen
```

Run the app locally with:

```bash
uv run uvicorn page2card.main:app --reload
```

The app serves at `http://127.0.0.1:8000`.

SQLite data defaults to `data/page2card.db`. Tests must use temporary databases and must not depend on or modify the local development database.

## Common Commands

Run these from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

If OpenAI SDK support is implemented, add it through `uv` so both `pyproject.toml` and `uv.lock` stay in sync.

## Issue Context

For the AI summary/card task, read:

- `README.md` for the starter app behavior and local commands.
- `PAGE2CARD_ISSUE.md` for the complete feature specification, tests, and acceptance criteria.
- GitHub Issue #4 for the concise tracking issue.

Do not copy the full specification into new docs or PR descriptions. Summarize the implemented changes and link back to the issue/spec when useful.

## Development Constraints

- Keep changes scoped to the active issue.
- Do not modify existing fetch, extraction, normalization, save, category, or delete behavior unless the issue explicitly requires it.
- Keep the existing FastAPI, Jinja2, SQLite, and `uv` project structure.
- Do not add a frontend framework, external CDN, or lightbox package. Use small native JavaScript only when needed.
- Do not replace SQLite.
- Do not save, log, echo, or persist user-provided OpenAI API keys in SQLite, cookies, HTML, logs, or files.
- Do not call real OpenAI APIs from tests. Use mocks or fakes.
- Treat article content as untrusted input. Preserve Jinja2 escaping and display AI summaries as plain text.
- Avoid path traversal risks for generated card images. Do not build filesystem paths directly from user-controlled values.
- Generated card image files must be ignored by git.

## AI Summary And Card Requirements

The summary feature should produce Traditional Chinese content with:

- A headline-style quote.
- A 2-5 sentence overview.
- 2-6 concise key points.

The card feature should:

- Use built-in card styles and social sizes defined in centralized data structures.
- Generate one or more shareable images through the OpenAI image API.
- Preserve selected style, size, card order, and card role.
- Reuse saved summaries and images instead of calling APIs on every page load.
- Show a clear note that AI-generated Chinese text in images may be imperfect and that the page text summary is authoritative.

## Verification

Before finishing code changes, run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

If a command cannot run in the current environment, report the command, the reason it failed, and any narrower verification that was completed.

## Expected Final Response

When completing a Cloud task, summarize:

- What changed.
- Which files or areas were touched.
- Verification commands and results.
- Any remaining limitations or follow-up work.
