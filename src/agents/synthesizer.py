"""Synthesis Agent — generates an executive summary of top results."""

from __future__ import annotations

from src.agents.state import SearchState
from src.utils.llm import llm_completion
from src.utils.prompts import load_prompt


def synthesis_agent(state: SearchState) -> SearchState:
    """Produce a structured summary of the top-ranked papers."""
    ranked = state.get("ranked_results", [])
    user_query = state["user_query"]

    if not ranked:
        return {**state, "summary": "No relevant papers found for your query."}

    # Format top 5 papers for the prompt
    top_papers = ranked[:5]
    papers_text = "\n\n".join(
        f"**{p.get('meta', {}).get('title', 'Untitled')}** (ID: {p.get('id', 'N/A')})\n{p.get('text', '')}"
        for p in top_papers
    )

    prompts = load_prompt("synthesizer")
    system_prompt = prompts["system"]
    user_prompt = prompts["user"].format(user_query=user_query, papers=papers_text)

    summary = llm_completion(system_prompt=system_prompt, user_prompt=user_prompt)

    return {**state, "summary": summary}
