"""Deterministic search engine core: BM25, FAISS vector search, and RRF fusion."""

from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


@dataclass
class Document:
    doc_id: str
    title: str
    abstract: str

    def __eq__(self, other):
        if not isinstance(other, Document):
            return NotImplemented
        return self.doc_id == other.doc_id and self.title == other.title and self.abstract == other.abstract


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        rankings: List of ranked doc_id lists (best first).
        k: RRF constant (default 60 per original paper).

    Returns:
        Sorted list of (doc_id, fused_score) tuples, highest score first.
    """
    if not rankings:
        return []

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rank + k)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class SearchEngine:
    """In-memory hybrid search engine combining BM25 and FAISS vector search."""

    def __init__(self, embedding_model: str = EMBEDDING_MODEL):
        self._embedding_model_name = embedding_model
        self._encoder: SentenceTransformer | None = None
        self._documents: list[Document] = []
        self._bm25: BM25Okapi | None = None
        self._faiss_index: faiss.IndexFlatIP | None = None
        self._doc_embeddings: np.ndarray | None = None

    @property
    def document_count(self) -> int:
        return len(self._documents)

    @property
    def encoder(self) -> SentenceTransformer:
        if self._encoder is None:
            self._encoder = SentenceTransformer(self._embedding_model_name)
        return self._encoder

    def index(self, documents: list[Document]) -> None:
        """Index a list of documents for both BM25 and vector search."""
        self._documents = list(documents)

        # BM25 index
        tokenized = [doc.abstract.lower().split() for doc in self._documents]
        self._bm25 = BM25Okapi(tokenized)

        # FAISS index
        abstracts = [doc.abstract for doc in self._documents]
        embeddings = self.encoder.encode(abstracts, normalize_embeddings=True)
        self._doc_embeddings = embeddings.astype(np.float32)

        dim = self._doc_embeddings.shape[1]
        self._faiss_index = faiss.IndexFlatIP(dim)
        self._faiss_index.add(self._doc_embeddings)

    def bm25_search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        """Lexical search using BM25 scoring."""
        if not self._documents or self._bm25 is None:
            return []

        tokenized_query = query.lower().split()
        scores = self._bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [(self._documents[i], float(scores[i])) for i in top_indices]

    def vector_search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        """Semantic search using FAISS inner-product similarity."""
        if not self._documents or self._faiss_index is None:
            return []

        query_embedding = self.encoder.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, indices = self._faiss_index.search(query_embedding, min(top_k, len(self._documents)))

        return [(self._documents[int(idx)], float(score)) for score, idx in zip(scores[0], indices[0]) if idx != -1]

    def hybrid_search(self, query: str, top_k: int = 10) -> list[tuple[Document, float]]:
        """Hybrid search combining BM25 and vector search via RRF."""
        if not self._documents:
            return []

        bm25_results = self.bm25_search(query, top_k=len(self._documents))
        vector_results = self.vector_search(query, top_k=len(self._documents))

        bm25_ranking = [doc.doc_id for doc, _ in bm25_results]
        vector_ranking = [doc.doc_id for doc, _ in vector_results]

        fused = reciprocal_rank_fusion([bm25_ranking, vector_ranking])

        doc_map = {doc.doc_id: doc for doc in self._documents}
        return [(doc_map[doc_id], score) for doc_id, score in fused[:top_k]]
