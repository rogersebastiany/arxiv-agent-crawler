"""Local JSON storage for saved articles."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STORAGE_PATH = Path.home() / ".local" / "share" / "arxiv-agent-crawler" / "saved_articles.json"


def _ensure_dir():
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _atomic_write(articles: list[dict]):
    """Write JSON atomically — write to temp file then rename, so a crash can't corrupt."""
    _ensure_dir()
    fd, tmp_path = tempfile.mkstemp(dir=STORAGE_PATH.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(articles, f, indent=2)
        Path(tmp_path).replace(STORAGE_PATH)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def load_saved() -> list[dict]:
    """Load all saved articles. Returns empty list if file is missing or corrupted."""
    if not STORAGE_PATH.exists():
        return []
    try:
        with open(STORAGE_PATH) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_article(paper: dict) -> bool:
    """Save an article. Returns False if already saved."""
    articles = load_saved()
    paper_id = paper.get("id", "")
    if any(a.get("id") == paper_id for a in articles):
        return False
    entry = {
        "id": paper_id,
        "title": paper.get("meta", {}).get("title", "Untitled"),
        "abstract": paper.get("text", ""),
        "score": paper.get("score", 0),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    articles.append(entry)
    _atomic_write(articles)
    return True


def remove_article(paper_id: str):
    """Remove a saved article by ID."""
    articles = load_saved()
    articles = [a for a in articles if a.get("id") != paper_id]
    _atomic_write(articles)


def is_saved(paper_id: str) -> bool:
    """Check if an article is already saved."""
    return any(a.get("id") == paper_id for a in load_saved())
