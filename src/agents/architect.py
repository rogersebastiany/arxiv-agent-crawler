"""Query Architect agent — translates user intent into arXiv API query syntax."""

from __future__ import annotations

from src.agents.state import SearchState
from src.utils.llm import llm_completion
from src.utils.prompts import load_prompt


def query_architect(state: SearchState) -> SearchState:
    """Generate or broaden an arXiv query from the user's natural language question."""
    prompts = load_prompt("query_architect")
    user_query = state["user_query"]
    broaden = state.get("broaden", False)

    if broaden and state.get("arxiv_query"):
        system_prompt = prompts["expand"].format(
            previous_query=state["arxiv_query"],
            user_query=user_query,
        )
        user_prompt = f"Broaden this search for: {user_query}"
    else:
        system_prompt = prompts["system"]
        user_prompt = prompts["user"].format(user_query=user_query)

    arxiv_query = llm_completion(system_prompt=system_prompt, user_prompt=user_prompt)

    return {
        **state,
        "arxiv_query": arxiv_query,
        "broaden": False,
        "retry_count": state.get("retry_count", 0),
    }
