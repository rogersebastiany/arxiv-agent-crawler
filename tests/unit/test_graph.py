"""Tests for the LangGraph pipeline structure."""

from src.main import build_graph, should_broaden


def test_graph_compiles():
    """The graph should compile without errors."""
    graph = build_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_should_broaden_returns_architect():
    state = {"broaden": True}
    assert should_broaden(state) == "query_architect"


def test_should_broaden_returns_synthesis():
    state = {"broaden": False}
    assert should_broaden(state) == "synthesis_agent"


def test_should_broaden_defaults_to_synthesis():
    state = {}
    assert should_broaden(state) == "synthesis_agent"
