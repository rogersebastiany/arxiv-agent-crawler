"""Tests for the Synthesis Agent — LLM calls are mocked."""

from unittest.mock import patch

from src.agents.synthesizer import synthesis_agent


@patch("src.agents.synthesizer.llm_completion")
def test_synthesizer_generates_summary(mock_llm):
    mock_llm.return_value = "## Key Findings\n- Agents improve CI/CD testing efficiency."
    state = {
        "user_query": "agents for CI/CD",
        "ranked_results": [
            {"id": "2401.00001", "text": "About agents.", "score": 0.9, "meta": {"title": "Agent Paper"}},
        ],
    }

    result = synthesis_agent(state)

    assert "Key Findings" in result["summary"]
    mock_llm.assert_called_once()


def test_synthesizer_handles_empty_results():
    state = {
        "user_query": "agents for CI/CD",
        "ranked_results": [],
    }

    result = synthesis_agent(state)

    assert "No relevant papers" in result["summary"]
