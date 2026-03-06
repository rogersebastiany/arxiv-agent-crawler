"""Shared LangGraph state definition for the search pipeline."""

from __future__ import annotations

from typing import TypedDict

from src.core.engine import Document


class SearchState(TypedDict, total=False):
    user_query: str
    arxiv_query: str
    broaden: bool
    retry_count: int
    raw_results: list[Document]
    ranked_results: list[dict]
    quality_score: float
    summary: str
    error: str | None
