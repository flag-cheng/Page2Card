"""Application configuration.

Values can be overridden with environment variables (see ``.env.example``).
This starter is intended for local, single-user use only.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root is two levels up: src/page2card/config.py -> project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# SQLite database location. Defaults to ``data/page2card.db``.
DATABASE_PATH = Path(
    os.getenv("PAGE2CARD_DB_PATH", str(PROJECT_ROOT / "data" / "page2card.db"))
)

# HTTP client limits used by the fetcher.
CONNECT_TIMEOUT = float(os.getenv("PAGE2CARD_CONNECT_TIMEOUT", "5.0"))
READ_TIMEOUT = float(os.getenv("PAGE2CARD_READ_TIMEOUT", "10.0"))

# Maximum response body size we will read, in bytes (default 2 MiB).
MAX_RESPONSE_BYTES = int(
    os.getenv("PAGE2CARD_MAX_RESPONSE_BYTES", str(2 * 1024 * 1024))
)

# Number of characters of body text to keep per captured article.
MAX_CONTENT_CHARS = int(os.getenv("PAGE2CARD_MAX_CONTENT_CHARS", "20000"))

# User-Agent sent with every outbound request. A browser-like UA improves
# compatibility with sites that reject unknown clients.
USER_AGENT = os.getenv(
    "PAGE2CARD_USER_AGENT",
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 "
        f"page2card/{__import__('page2card').__version__}"
    ),
)
