"""FastAPI application exposing the search pipeline and serving the web UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.main import search
from src.storage import is_saved, load_saved, remove_article, save_article

app = FastAPI(title="arXiv Agent Crawler", version="0.1.0")


# --- Search ---


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language research question")


class SearchResponse(BaseModel):
    query: str
    arxiv_query: str
    quality_score: float
    summary: str
    top_results: list[dict]
    retry_count: int


@app.post("/api/search", response_model=SearchResponse)
def run_search(request: SearchRequest):
    """Run the full search pipeline and return results."""
    result = search(request.query)
    return SearchResponse(
        query=result["user_query"],
        arxiv_query=result.get("arxiv_query", ""),
        quality_score=result.get("quality_score", 0.0),
        summary=result.get("summary", ""),
        top_results=result.get("ranked_results", [])[:20],
        retry_count=result.get("retry_count", 0),
    )


# --- Saved articles ---


class SaveRequest(BaseModel):
    id: str
    text: str = ""
    score: float = 0.0
    meta: dict = {}


@app.get("/api/saved")
def get_saved():
    return load_saved()


@app.post("/api/saved")
def save(request: SaveRequest):
    paper = request.model_dump()
    saved = save_article(paper)
    return {"saved": saved}


@app.delete("/api/saved/{paper_id}")
def delete_saved(paper_id: str):
    remove_article(paper_id)
    return {"removed": True}


@app.get("/api/saved/{paper_id}/check")
def check_saved(paper_id: str):
    return {"saved": is_saved(paper_id)}


# --- Health ---


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Static files (web UI) — must be last ---

WEB_DIR = Path(__file__).resolve().parent.parent.parent / "ui" / "web"
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
