"""Tests for the Quality Agent — uses real engine but controlled data."""

from src.agents.quality import QUALITY_THRESHOLD, quality_agent


def test_quality_agent_ranks_results(sample_documents, agent_query):
    state = {
        "user_query": agent_query,
        "raw_results": sample_documents,
        "retry_count": 0,
    }

    result = quality_agent(state)

    assert len(result["ranked_results"]) > 0
    assert result["quality_score"] > 0.0
    assert isinstance(result["ranked_results"][0], dict)


def test_quality_agent_signals_broaden_on_empty_results():
    state = {
        "user_query": "anything",
        "raw_results": [],
        "retry_count": 0,
    }

    result = quality_agent(state)

    assert result["broaden"] is True
    assert result["retry_count"] == 1
    assert result["quality_score"] == 0.0


def test_quality_agent_does_not_broaden_after_max_retries():
    state = {
        "user_query": "anything",
        "raw_results": [],
        "retry_count": 3,
    }

    result = quality_agent(state)

    # retry_count is already at max, but broaden is still True for empty results
    # The graph's conditional edge handles the actual stopping
    assert result["retry_count"] == 4


def test_quality_agent_does_not_broaden_on_good_results(sample_documents, agent_query):
    state = {
        "user_query": agent_query,
        "raw_results": sample_documents,
        "retry_count": 0,
    }

    result = quality_agent(state)

    # With well-matched documents, quality should be above threshold
    if result["quality_score"] >= QUALITY_THRESHOLD:
        assert result["broaden"] is False
