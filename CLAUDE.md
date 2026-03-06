# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

An arXiv "Google-like" search engine that uses AI agents to translate user intent into precise arXiv API queries, then applies a local hybrid retrieval funnel to return highly relevant academic papers.

**Pipeline:** `arXiv API → FAISS (in-memory) → BM25 → RRF → FlashRank → Final Result`

## Commands

### Setup
```bash
uv sync                          # Install all dependencies
cp .env.example .env             # Configure API keys
```

### Development
```bash
uv run uvicorn src.api.main:app --reload   # Run API server
docker compose -f docker/docker-compose.yml up   # Run full stack (API + LangFuse)
```

### Testing
```bash
uv run pytest tests/unit/                  # Unit tests only
uv run pytest tests/unit/test_engine.py   # Single test file
uv run pytest -k "test_rrf"               # Single test by name
uv run promptfoo eval tests/evals/        # Eval gate (semantic/intent tests)
```

### Linting (CI enforced — must pass before commit)
```bash
uv run ruff check src/ tests/
uv run black --check src/ tests/
uv run black src/ tests/          # Auto-fix formatting
```

## Architecture

### Agent Nodes (`src/agents/`)
LangGraph-orchestrated pipeline with 4 nodes. Each node must be independently testable in isolation.

| Node | File | Role |
|---|---|---|
| Query Architect | `architect.py` | LLM (via LiteLLM) translates user query into arXiv API syntax (e.g., `abs:(...) AND cat:cs.AI`) |
| Search Agent | `searcher.py` | Calls arXiv Python wrapper; caches results in-memory by query hash |
| Quality Agent | `quality.py` | Runs FAISS semantic search + BM25, fuses with RRF, reranks top-20 with FlashRank |
| Synthesis Agent | `synthesizer.py` | LLM summarizes top results into executive insight (uses prompt caching) |

**Smart Loop:** If Quality Agent finds no results above threshold (score < 0.3), it signals the Query Architect to broaden the query — a self-correction cycle.

### Search Engine Core (`src/core/`)
Deterministic, pure-logic components — implement with TDD (write tests first):
- `engine.py` — BM25 (`rank_bm25`) + FAISS index + RRF fusion math
- `embedding.py` — SentenceTransformers wrapper (`BAAI/bge-small-en-v1.5`)
- `reranker.py` — FlashRank wrapper (`ms-marco-MiniLM-L-12-v2`)

### Key Conventions

**Prompts:** All LLM prompts live in `/prompts/` as YAML/JSON. Never hardcode prompts in Python files.

**Testing split:**
- `tests/unit/` — `pytest` with deterministic assertions for all non-AI code (parsers, RRF math, filters). All external API calls (arXiv, LiteLLM) must be mocked with `unittest.mock` or `responses`.
- `tests/evals/` — `promptfoo`/`deepeval` semantic evals against `golden_dataset.json` (10-20 edge-case queries). CI passes only if relevance score > 0.8.

**Resiliency:** Use `tenacity` for all external API calls (arXiv, LLM providers). Every agent node must signal "insufficient data" rather than hallucinate.

**Observability:** Instrument all agent nodes with LangFuse callbacks from the start.

**Dependencies:** Managed with `uv` via `pyproject.toml`. Container-first: use Docker/docker-compose.

### Claude-Specific Capabilities to Leverage
- **Parallel tool calling** in `QueryArchitect`: bind multiple tools (keyword expansion + category filtering) for a single-turn multi-tool response.
- **Prompt caching**: Cache `SummarizerTool` system instructions and few-shot examples to cut input token costs on the Synthesis Agent.
- **Extended thinking**: Use in `QualityAgent` to reason about whether a paper's methodology matches the user's specific constraints before assigning a confidence score.
