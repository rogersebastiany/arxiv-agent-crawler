"""Search Agent — fetches papers from arXiv API with caching."""

from __future__ import annotations

import hashlib

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.state import SearchState
from src.core.engine import Document

# Simple in-memory cache keyed by query hash
_cache: dict[str, list[Document]] = {}

MAX_RESULTS = 100


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _fetch_arxiv(query: str, max_results: int = MAX_RESULTS) -> list[Document]:
    """Fetch papers from the arXiv API."""
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
    results = []
    for paper in client.results(search):
        results.append(
            Document(
                doc_id=paper.entry_id.split("/")[-1],
                title=paper.title,
                abstract=paper.summary,
            )
        )
    return results


def search_agent(state: SearchState) -> SearchState:
    """Fetch candidate papers from arXiv based on the generated query."""
    query = state.get("arxiv_query", "")
    if not query:
        return {**state, "raw_results": [], "error": "No arxiv_query provided"}

    cache_key = hashlib.sha256(query.encode()).hexdigest()

    if cache_key in _cache:
        results = _cache[cache_key]
    else:
        try:
            results = _fetch_arxiv(query)
            _cache[cache_key] = results
        except Exception as e:
            return {**state, "raw_results": [], "error": f"arXiv fetch failed: {e}"}

    return {**state, "raw_results": results, "error": None}
