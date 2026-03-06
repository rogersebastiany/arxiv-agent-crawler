"""TDD tests for the deterministic search engine core.

Tests cover: BM25 scoring, FAISS vector search, RRF fusion, and the full pipeline.
All tests use deterministic assertions — no AI calls.
"""

from src.core.engine import Document, SearchEngine, reciprocal_rank_fusion


class TestDocument:
    def test_document_creation(self):
        doc = Document(doc_id="123", title="Test", abstract="Some abstract text")
        assert doc.doc_id == "123"
        assert doc.title == "Test"
        assert doc.abstract == "Some abstract text"

    def test_document_equality(self):
        d1 = Document(doc_id="123", title="A", abstract="B")
        d2 = Document(doc_id="123", title="A", abstract="B")
        assert d1 == d2


class TestRRF:
    def test_rrf_single_ranking(self):
        """RRF with a single ranking should preserve order."""
        rankings = [["doc_a", "doc_b", "doc_c"]]
        result = reciprocal_rank_fusion(rankings, k=60)
        ids = [doc_id for doc_id, _ in result]
        assert ids == ["doc_a", "doc_b", "doc_c"]

    def test_rrf_two_rankings_agreement(self):
        """When both rankings agree, RRF should preserve that order."""
        rankings = [
            ["doc_a", "doc_b", "doc_c"],
            ["doc_a", "doc_b", "doc_c"],
        ]
        result = reciprocal_rank_fusion(rankings, k=60)
        ids = [doc_id for doc_id, _ in result]
        assert ids[0] == "doc_a"

    def test_rrf_two_rankings_disagreement(self):
        """When rankings disagree, the doc appearing in both should rank higher."""
        rankings = [
            ["doc_a", "doc_b"],
            ["doc_b", "doc_c"],
        ]
        result = reciprocal_rank_fusion(rankings, k=60)
        ids = [doc_id for doc_id, _ in result]
        # doc_b appears in both rankings — it should be ranked first
        assert ids[0] == "doc_b"

    def test_rrf_scores_decrease(self):
        """RRF scores should be monotonically decreasing."""
        rankings = [["a", "b", "c", "d"]]
        result = reciprocal_rank_fusion(rankings, k=60)
        scores = [score for _, score in result]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_rrf_empty_rankings(self):
        result = reciprocal_rank_fusion([], k=60)
        assert result == []

    def test_rrf_k_parameter_affects_scores(self):
        """Different k values should produce different absolute scores."""
        rankings = [["a", "b", "c"]]
        result_k1 = reciprocal_rank_fusion(rankings, k=1)
        result_k60 = reciprocal_rank_fusion(rankings, k=60)
        # With k=1: 1/(1+1)=0.5, 1/(2+1)=0.33...
        # With k=60: 1/(1+60)=0.0164, 1/(2+60)=0.0161...
        assert result_k1[0][1] != result_k60[0][1]


class TestSearchEngine:
    def test_index_documents(self, sample_documents):
        """Engine should successfully index documents."""
        engine = SearchEngine()
        engine.index(sample_documents)
        assert engine.document_count == len(sample_documents)

    def test_bm25_search(self, sample_documents, agent_query):
        """BM25 should rank agent/CI-CD docs higher for the agent query."""
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.bm25_search(agent_query, top_k=3)
        result_ids = [doc.doc_id for doc, _ in results]
        # The two agent/CI-CD papers should be in the top results
        assert "2401.00001" in result_ids
        assert "2401.00004" in result_ids

    def test_bm25_returns_scores(self, sample_documents, agent_query):
        """BM25 results should include non-negative scores."""
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.bm25_search(agent_query, top_k=3)
        for _, score in results:
            assert score >= 0.0

    def test_bm25_top_k_limits_results(self, sample_documents, agent_query):
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.bm25_search(agent_query, top_k=2)
        assert len(results) == 2

    def test_vector_search(self, sample_documents, agent_query):
        """FAISS vector search should find semantically relevant docs."""
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.vector_search(agent_query, top_k=3)
        result_ids = [doc.doc_id for doc, _ in results]
        # Agent/CI-CD papers should rank high on semantic similarity
        assert "2401.00001" in result_ids or "2401.00004" in result_ids

    def test_vector_search_returns_scores(self, sample_documents, agent_query):
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.vector_search(agent_query, top_k=3)
        for _, score in results:
            assert isinstance(score, float)

    def test_hybrid_search(self, sample_documents, agent_query):
        """Hybrid search (BM25 + vector + RRF) should surface the best docs."""
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.hybrid_search(agent_query, top_k=3)
        result_ids = [doc.doc_id for doc, _ in results]
        # With fusion, both relevant papers should surface
        assert "2401.00001" in result_ids
        assert "2401.00004" in result_ids

    def test_hybrid_search_top_k(self, sample_documents, agent_query):
        engine = SearchEngine()
        engine.index(sample_documents)
        results = engine.hybrid_search(agent_query, top_k=2)
        assert len(results) == 2

    def test_search_empty_index(self):
        """Searching before indexing should return empty results."""
        engine = SearchEngine()
        results = engine.hybrid_search("anything", top_k=5)
        assert results == []

    def test_reindex_replaces_old_data(self, sample_documents):
        """Calling index again should replace the previous index."""
        engine = SearchEngine()
        engine.index(sample_documents)
        assert engine.document_count == 5

        engine.index(sample_documents[:2])
        assert engine.document_count == 2
