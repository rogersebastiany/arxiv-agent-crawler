"""FastAPI application exposing the search pipeline."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.main import search

app = FastAPI(title="arXiv Agent Crawler", version="0.1.0")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language research question")


class SearchResponse(BaseModel):
    query: str
    arxiv_query: str
    quality_score: float
    summary: str
    top_results: list[dict]
    retry_count: int


@app.post("/search", response_model=SearchResponse)
def run_search(request: SearchRequest):
    """Run the full search pipeline and return results."""
    result = search(request.query)
    return SearchResponse(
        query=result["user_query"],
        arxiv_query=result.get("arxiv_query", ""),
        quality_score=result.get("quality_score", 0.0),
        summary=result.get("summary", ""),
        top_results=result.get("ranked_results", [])[:10],
        retry_count=result.get("retry_count", 0),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
