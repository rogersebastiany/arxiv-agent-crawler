"""Tests for the Search Agent — arXiv API calls are mocked."""

from unittest.mock import patch

from src.agents.searcher import _cache, search_agent
from src.core.engine import Document


@patch("src.agents.searcher._fetch_arxiv")
def test_searcher_fetches_results(mock_fetch):
    mock_fetch.return_value = [
        Document(doc_id="2401.00001", title="Test Paper", abstract="About agents and testing."),
    ]
    state = {"user_query": "agents", "arxiv_query": "abs:agents"}

    result = search_agent(state)

    assert len(result["raw_results"]) == 1
    assert result["raw_results"][0].doc_id == "2401.00001"
    assert result["error"] is None


def test_searcher_returns_error_without_query():
    state = {"user_query": "agents", "arxiv_query": ""}

    result = search_agent(state)

    assert result["raw_results"] == []
    assert "No arxiv_query" in result["error"]


@patch("src.agents.searcher._fetch_arxiv")
def test_searcher_uses_cache(mock_fetch):
    _cache.clear()
    docs = [Document(doc_id="cached", title="Cached", abstract="Cached paper.")]
    mock_fetch.return_value = docs
    state = {"user_query": "agents", "arxiv_query": "abs:cached_test_query"}

    # First call populates cache
    search_agent(state)
    # Second call should use cache
    result = search_agent(state)

    assert mock_fetch.call_count == 1
    assert result["raw_results"][0].doc_id == "cached"
    _cache.clear()
