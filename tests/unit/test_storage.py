"""Tests for the saved articles storage module."""

import json
from unittest.mock import patch

import pytest

from src.storage import is_saved, load_saved, remove_article, save_article


@pytest.fixture
def tmp_storage(tmp_path):
    """Patch STORAGE_PATH to use a temp directory."""
    storage_file = tmp_path / "saved_articles.json"
    with patch("src.storage.STORAGE_PATH", storage_file):
        yield storage_file


@pytest.fixture
def sample_paper():
    return {
        "id": "2401.00001",
        "text": "About agents and testing.",
        "score": 0.95,
        "meta": {"title": "Agent Paper"},
    }


class TestSaveArticle:
    def test_save_new_article(self, tmp_storage, sample_paper):
        assert save_article(sample_paper) is True
        articles = load_saved()
        assert len(articles) == 1
        assert articles[0]["id"] == "2401.00001"
        assert articles[0]["title"] == "Agent Paper"

    def test_save_duplicate_returns_false(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        assert save_article(sample_paper) is False
        assert len(load_saved()) == 1

    def test_save_multiple_articles(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        other = {**sample_paper, "id": "2401.00002", "meta": {"title": "Other Paper"}}
        save_article(other)
        assert len(load_saved()) == 2


class TestLoadSaved:
    def test_load_empty(self, tmp_storage):
        assert load_saved() == []

    def test_load_missing_file(self, tmp_storage):
        assert load_saved() == []

    def test_load_corrupted_json(self, tmp_storage):
        tmp_storage.write_text("this is not json{{{")
        assert load_saved() == []

    def test_load_truncated_json(self, tmp_storage):
        tmp_storage.write_text('[{"id": "123", "title": "trunc')
        assert load_saved() == []


class TestRemoveArticle:
    def test_remove_existing(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        remove_article("2401.00001")
        assert load_saved() == []

    def test_remove_nonexistent(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        remove_article("nonexistent")
        assert len(load_saved()) == 1


class TestIsSaved:
    def test_is_saved_true(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        assert is_saved("2401.00001") is True

    def test_is_saved_false(self, tmp_storage):
        assert is_saved("2401.00001") is False


class TestAtomicWrite:
    def test_file_not_corrupted_after_save(self, tmp_storage, sample_paper):
        save_article(sample_paper)
        # File should be valid JSON
        with open(tmp_storage) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
