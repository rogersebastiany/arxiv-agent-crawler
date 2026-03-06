"""FlashRank reranking wrapper."""

from __future__ import annotations

from flashrank import Ranker, RerankRequest

DEFAULT_MODEL = "ms-marco-MiniLM-L-12-v2"


class RerankerService:
    """Wraps FlashRank for cross-encoder reranking of search results."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self._ranker = Ranker(model_name=model_name)

    def rerank(
        self,
        query: str,
        passages: list[dict],
        top_k: int = 20,
    ) -> list[dict]:
        """Rerank passages against a query.

        Args:
            query: The user's original query.
            passages: List of dicts with at minimum an "id" and "text" key.
            top_k: Number of top results to return.

        Returns:
            Sorted list of passage dicts with an added "score" key.
        """
        if not passages:
            return []

        request = RerankRequest(query=query, passages=passages)
        results = self._ranker.rerank(request)
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
