"""LangGraph graph definition — the full search pipeline with smart broadening loop."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents.architect import query_architect
from src.utils.callbacks import configure_observability

configure_observability()
from src.agents.quality import quality_agent
from src.agents.searcher import search_agent
from src.agents.state import SearchState
from src.agents.synthesizer import synthesis_agent


def should_broaden(state: SearchState) -> str:
    """Conditional edge: route back to architect if quality is too low."""
    if state.get("broaden", False):
        return "query_architect"
    return "synthesis_agent"


def build_graph() -> StateGraph:
    """Construct the search pipeline graph."""
    graph = StateGraph(SearchState)

    graph.add_node("query_architect", query_architect)
    graph.add_node("search_agent", search_agent)
    graph.add_node("quality_agent", quality_agent)
    graph.add_node("synthesis_agent", synthesis_agent)

    graph.set_entry_point("query_architect")
    graph.add_edge("query_architect", "search_agent")
    graph.add_edge("search_agent", "quality_agent")
    graph.add_conditional_edges("quality_agent", should_broaden)
    graph.add_edge("synthesis_agent", END)

    return graph


# Compiled graph ready for invocation
app = build_graph().compile()


STEPS = [
    ("query_architect", "Building search query...", 25),
    ("search_agent", "Fetching papers from arXiv...", 50),
    ("quality_agent", "Ranking and filtering results...", 75),
    ("synthesis_agent", "Generating summary...", 95),
]


def _initial_state(user_query: str) -> SearchState:
    return {
        "user_query": user_query,
        "arxiv_query": "",
        "broaden": False,
        "retry_count": 0,
        "raw_results": [],
        "ranked_results": [],
        "quality_score": 0.0,
        "summary": "",
        "error": None,
    }


def search(user_query: str) -> SearchState:
    """Run the full search pipeline for a user query."""
    return app.invoke(_initial_state(user_query))


def search_with_progress(user_query: str):
    """Run the pipeline step-by-step, yielding (step_name, label, percent, state) after each.

    The final yield has percent=100 and the complete state.
    """
    agents = {
        "query_architect": query_architect,
        "search_agent": search_agent,
        "quality_agent": quality_agent,
        "synthesis_agent": synthesis_agent,
    }

    state = _initial_state(user_query)

    for step_name, label, percent in STEPS:
        yield step_name, label, percent, None
        state = {**state, **agents[step_name](state)}

        # Handle broadening loop
        if step_name == "quality_agent" and state.get("broaden", False):
            yield "query_architect", "Broadening query...", 30, None
            state = {**state, **query_architect(state)}
            yield "search_agent", "Re-fetching papers...", 50, None
            state = {**state, **search_agent(state)}
            yield "quality_agent", "Re-ranking results...", 75, None
            state = {**state, **quality_agent(state)}

    yield "done", "Done", 100, state
