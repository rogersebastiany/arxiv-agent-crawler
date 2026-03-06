"""Tests for the Query Architect agent — LLM calls are mocked."""

from unittest.mock import patch

from src.agents.architect import query_architect


@patch("src.agents.architect.llm_completion")
def test_architect_generates_query(mock_llm):
    mock_llm.return_value = 'abs:("autonomous agents") AND abs:("CI/CD") AND cat:cs.AI'
    state = {"user_query": "agents for CI/CD testing", "broaden": False, "retry_count": 0}

    result = query_architect(state)

    assert "arxiv_query" in result
    assert "abs:" in result["arxiv_query"]
    mock_llm.assert_called_once()


@patch("src.agents.architect.llm_completion")
def test_architect_broadens_query(mock_llm):
    mock_llm.return_value = 'abs:("agents" OR "automation") AND abs:("testing")'
    state = {
        "user_query": "agents for CI/CD testing",
        "arxiv_query": 'abs:("autonomous agents") AND abs:("CI/CD") AND cat:cs.AI',
        "broaden": True,
        "retry_count": 1,
    }

    result = query_architect(state)

    assert result["broaden"] is False
    assert "arxiv_query" in result
    mock_llm.assert_called_once()
    # System prompt should contain the previous query (expand mode)
    call_kwargs = mock_llm.call_args
    assert "CI/CD" in call_kwargs.kwargs.get("system_prompt", "") or "CI/CD" in str(call_kwargs)
