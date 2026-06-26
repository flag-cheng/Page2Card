"""Shared pytest fixtures.

Tests use an isolated temporary database and never touch the real
``data/page2card.db``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from page2card import database
from page2card.repository import Repository

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def repo(db_path: Path) -> Repository:
    conn = database.connect(db_path)
    repository = Repository(conn)
    yield repository
    conn.close()
