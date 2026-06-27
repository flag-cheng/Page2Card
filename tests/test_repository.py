"""Tests for the article repository."""

from __future__ import annotations

import re

from page2card.repository import Repository


def test_add_and_get_article(repo: Repository):
    article = repo.add_article("https://example.com/a", "標題", "內文內容", "科技")
    assert article.id is not None
    fetched = repo.get_article(article.id)
    assert fetched.title == "標題"
    assert fetched.category == "科技"


def test_created_at_format_has_no_timezone_suffix(repo: Repository):
    article = repo.add_article("https://example.com/a", "標題", "x", None)
    # "YYYY-MM-DD HH:MM:SS" — a space separator, no "T" and no offset.
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", article.created_at)


def test_published_at_round_trips(repo: Repository):
    article = repo.add_article(
        "https://example.com/a", "標題", "x", None, "2026-06-25 08:30:00"
    )
    assert repo.get_article(article.id).published_at == "2026-06-25 08:30:00"


def test_published_at_defaults_to_none(repo: Repository):
    article = repo.add_article("https://example.com/a", "標題", "x", None)
    assert repo.get_article(article.id).published_at is None


def test_list_articles_newest_first(repo: Repository):
    repo.add_article("https://example.com/1", "第一篇", "x", None)
    repo.add_article("https://example.com/2", "第二篇", "y", None)
    titles = [a.title for a in repo.list_articles()]
    assert titles == ["第二篇", "第一篇"]


def test_list_articles_filtered_by_category(repo: Repository):
    repo.add_article("https://example.com/1", "科技文", "x", "科技")
    repo.add_article("https://example.com/2", "財經文", "y", "財經")
    tech = repo.list_articles(category="科技")
    assert [a.title for a in tech] == ["科技文"]


def test_list_categories_distinct_sorted(repo: Repository):
    repo.add_article("https://example.com/1", "a", "x", "科技")
    repo.add_article("https://example.com/2", "b", "y", "科技")
    repo.add_article("https://example.com/3", "c", "z", "財經")
    repo.add_article("https://example.com/4", "d", "w", None)
    assert repo.list_categories() == ["科技", "財經"]


def test_delete_article(repo: Repository):
    article = repo.add_article("https://example.com/a", "標題", "內文", None)
    assert repo.delete_article(article.id) is True
    assert repo.get_article(article.id) is None
    assert repo.delete_article(article.id) is False
