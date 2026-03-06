"""Quality Agent — hybrid search, reranking, and threshold gating."""

from __future__ import annotations

from src.agents.state import SearchState
from src.core.engine import SearchEngine
from src.core.reranker import RerankerService

QUALITY_THRESHOLD = 0.3
MAX_RETRIES = 3

# Shared instances (initialized once, reused across calls)
_engine = SearchEngine()
_reranker = RerankerService()


def quality_agent(state: SearchState) -> SearchState:
    """Run hybrid search + reranking on fetched papers, gate on quality threshold."""
    raw_results = state.get("raw_results", [])

    if not raw_results:
        return {
            **state,
            "ranked_results": [],
            "quality_score": 0.0,
            "broaden": True,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    user_query = state["user_query"]

    # Index and run hybrid search
    _engine.index(raw_results)
    hybrid_results = _engine.hybrid_search(user_query, top_k=20)

    # Prepare passages for FlashRank reranking
    passages = [{"id": doc.doc_id, "text": doc.abstract, "meta": {"title": doc.title}} for doc, _ in hybrid_results]

    reranked = _reranker.rerank(query=user_query, passages=passages, top_k=20)

    # Extract top quality score
    top_score = reranked[0]["score"] if reranked else 0.0
    retry_count = state.get("retry_count", 0)

    # Gate: if quality is too low and we haven't exhausted retries, signal broadening
    should_broaden = bool(top_score < QUALITY_THRESHOLD and retry_count < MAX_RETRIES)

    return {
        **state,
        "ranked_results": reranked,
        "quality_score": top_score,
        "broaden": should_broaden,
        "retry_count": retry_count + (1 if should_broaden else 0),
    }
