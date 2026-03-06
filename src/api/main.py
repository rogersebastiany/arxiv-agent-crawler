"""FastAPI application exposing the search pipeline and serving the web UI."""

from __future__ import annotations

from pathlib import Path

import json

import numpy as np
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from src.main import search, search_with_progress
from src.storage import is_saved, load_saved, remove_article, save_article

app = FastAPI(title="arXiv Agent Crawler", version="0.1.0")


def _sanitize(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


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
        quality_score=float(result.get("quality_score", 0.0)),
        summary=result.get("summary", ""),
        top_results=_sanitize(result.get("ranked_results", [])[:20]),
        retry_count=result.get("retry_count", 0),
    )


@app.post("/api/search/stream")
def run_search_stream(request: SearchRequest):
    """SSE endpoint that streams progress updates during search."""

    def event_stream():
        for step_name, label, percent, state in search_with_progress(request.query):
            if state is None:
                payload = json.dumps({"step": step_name, "label": label, "percent": percent})
                yield f"event: progress\ndata: {payload}\n\n"
            else:
                result = _sanitize(
                    {
                        "query": state["user_query"],
                        "arxiv_query": state.get("arxiv_query", ""),
                        "quality_score": float(state.get("quality_score", 0.0)),
                        "summary": state.get("summary", ""),
                        "top_results": state.get("ranked_results", [])[:20],
                        "retry_count": state.get("retry_count", 0),
                    }
                )
                yield f"event: result\ndata: {json.dumps(result)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
