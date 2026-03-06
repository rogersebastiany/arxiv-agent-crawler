arXiv will act as a *Search Provider* while we will build the *Search Engine*. arXiv accepts search based on key-words, while we will do *Hybrid Search* and *Re-ranking* locally. We will be the google for arXiv.

The flow of this application is as follows:
`API arXiv` $\rightarrow$ `FAISS (In-memory)` $\rightarrow$ `BM25` $\rightarrow$ `RRF` $\rightarrow$ `FlashRank` $\rightarrow$ `Resultado Final`

Detais:
1. LLM-as-a-Query-Builder
		arXiv doesn't understand semantic search. So our first step is to use a LLM to translate the user's wish into a perfect query for the arXiv's API.
		- User sends a query, for example: "I want to know how people are using agents to run tests in CI/CD"
		- LLM (Query Builder): Transforms this in `abs:("autonomous agents" OR "LLM agents") AND abs:("CI/CD" OR "automated testing") AND cat:cs.AI`, for example.
2. Candidate Retrieval
		fetch arXiv api with a high volume of possible article candidates. If possible, 100 articles abstracts/metadata loaded in RAM.
3. Local funel
		- Local Vector Search: generate the embeddings for all abstracts and compare with the embedded user's initial query.
		- Local BM25: Run `rank_bm25` in the abstracts against the user's embedded initial query.
		- Fusion (RRF): Combine both vectors to create a unified list of possible articles
		- Re-ranking: The top 20 results are fetched into the Cross-Encoder for the final list.
		  
---
#### 1. Agent orchestration:

	We want to have a "google-like" feel to the app, so we will have agents. equiring loops, state checks, and iterative refinement. It enables deterministic, testable management of your search pipeline

#### 2. Retrieval & Indexing (The Engine)

- **arXiv Client:** Use the official Python wrapper; simple and reliable.
    
- **Lexical Search:** Use `rank_bm25` for local BM25 scoring.
    
- **Semantic Search:** Use `sentence-transformers` with the BGE family (e.g., `BAAI/bge-small-en-v1.5`). They are compact, fast, and SOTA for academic English.
    
- **In-Memory Storage:** **FAISS** (by Meta). Avoid heavy databases (like Pinecone/Qdrant) at runtime; FAISS is perfect for keeping your top 100 API results in memory.
    

### 3. Intelligence (The Precision Funnel)

- **LLM (Query Builder):** **LiteLLM**. A wrapper to abstract API calls. It prevents vendor lock-in and allows you to swap providers easily. Stick to cost-effective, fast models (e.g., `gpt-4o-mini` or `claude-3-haiku`).
    
- **Reranking:** **FlashRank**. Stop building manual cross-encoders. This library is highly optimized, `prod-ready`, and delivers results in milliseconds using models like `ms-marco-MiniLM-L-12-v2`.

---

##### Agent-Tool Mapping

We will be using LangGraph for agent orchestration.

|**Agent (Node)**|**Primary Function**|**Suggested Tools**|
|---|---|---|
|**Query Architect**|Translates user intent into technical parameters.|`QueryExpanderTool` (LLM-based)|
|**Search Agent**|Manages API interaction & raw state.|`ArxivFetchTool` (API wrapper)|
|**Quality Agent**|Noise reduction & re-ranking.|`FlashRankTool`, `SemanticFilter`|
|**Synthesis Agent**|Final output generation & insight formatting.|`SummarizerTool` (LLM-based)|

### Tool Specifications

#### 1. Query Architect (`QueryExpanderTool`)

- **Purpose:** Takes simple user input (e.g., "autonomous agents") and uses a fast LLM (GPT-4o-mini) to generate technical search queries (e.g., ["autonomous agents", "LLM reasoning", "multi-agent systems"]).
    
- **Why it's vital:** arXiv is keyword-sensitive. This tool prevents "missed hits" caused by oversimplified terminology.
    

#### 2. Search Agent (`ArxivFetchTool`)

- **Purpose:** The operational arm. Executes calls to the official arXiv API and converts raw JSON into structured Python objects (title, abstract, date, links).
    
- **Optimization:** Implement simple in-memory caching (dict or JSON) to prevent redundant API calls for recurring searches.
    

#### 3. Quality Agent (`FlashRankTool`)

- **Purpose:** The "cleaner." Takes raw results (e.g., 50 abstracts) and runs FlashRank to score them against the user’s original query.
    
- **Function:** Sorts by relevance and drops results below a predefined confidence threshold to eliminate false positives.
    

#### 4. Synthesis Agent (`SummarizerTool`)

- **Purpose:** Converts top results (e.g., Top 5) into an executive summary.
    
- **Why it's vital:** Users want actionable insights, not just a list of links. This tool turns raw data into knowledge.

### Orchestration: The LangGraph Flow

Define the workflow via nodes and edges:

1. **Start** $\rightarrow$ **Query Architect** (Define strategy).
    
2. **Query Architect** $\rightarrow$ **Search Agent** (Execute strategy).
    
3. **Search Agent** $\rightarrow$ **Quality Agent** (Filter/Rank).
    
4. **Quality Agent** $\rightarrow$ **Synthesis Agent** (Generate output) $\rightarrow$ **End**.

#### The "Smart Loop" (Autonomous Self-Correction)

Add a conditional edge: If the **Quality Agent** determines no articles meet the threshold (e.g., score < 0.3), trigger a signal back to the **Query Architect** to trigger a "broaden query" loop. This enables your system to self-correct and perform truly autonomous research.

### Human in the Loop 
		Add, and also keep the query, document_id and feedback stored in a simple database.

---
### 4. Stack Summary

| **Layer**         | **Tool**             | **Rationale**                                         |
| ----------------- | -------------------- | ----------------------------------------------------- |
| **Orchestration** | LangGraph            | Complex state management for agents.                  |
| **API Client**    | arxiv                | Official, stable, and straightforward.                |
| **Embeddings**    | SentenceTransformers | Local execution (zero API cost).                      |
| **Reranker**      | FlashRank            | Optimized, fast, and "prod-ready."                    |
| **LLM Framework** | LiteLLM              | Provider agnostic; effortless model swapping.         |
| **Interface**     | FastAPI              | Ideal for exposing your crawler as a backend service. |

---
#### Project Core Philosophy

- **Deterministic Logic (TDD):** All non-AI components (parsers, data structures, RRF algorithms, filters) MUST be tested with `pytest` using deterministic assertions.
    
- **Semantic Intelligence (Evals):** AI outputs and agent decisions (prompt results, extraction quality) MUST be tested using **Eval Gates** (e.g., Promptfoo/DeepEval). We test for _relevance and intent_, not exact string matching.
- Observability: Use Lang Fuse
- Resiliency: Always think about resiliency. For example, while fetching data, use a library such as `tenacity` for managing retries and rate limits.
## 2. Testing Infrastructure

- **Mocking:** All external API calls (arXiv, OpenAI/Anthropic APIs) MUST be mocked during unit tests using `unittest.mock` or `responses`. No live calls in the test suite.
    
- **Prompt Management:** Prompts are logic. All prompts must be stored in `/prompts` (YAML/JSON), never hardcoded in the logic.
    
- **The "Golden Dataset":** Maintain a `tests/evals/golden_dataset.json` file. This dataset contains 10-20 "Edge Case" queries (vague, technical, multi-topic). All CI pipelines must pass this suite.
    

## 3. The CI/CD Pipeline (GitHub Actions)

Every `git push` must trigger the following automated sequence:

1. **Linting & Style:** Run `ruff` and `black`. If formatting is off, the build fails.
    
2. **Unit Tests (`pytest`):** Run all logic-based tests. Verification of parsing, RRF math, and filtering logic.
    
3. **Eval Gate:** Run the `promptfoo`/`deepeval` suite against the Golden Dataset.
    
    - **Success Condition:** All tests must maintain a relevance score > **0.8** (or defined threshold).
        
    - **Failure Condition:** If the AI agent output deviates from the intent or breaks formatting, the build fails.
        

## 4. Development Standards

- **Decoupling:** LangGraph nodes must be modular. Test each agent node in isolation before testing the full graph.
    
- **Environment:** Use `.env.example` for all required keys. Never commit secrets.
    
- **Error Handling:** Every node must have a fallback mechanism. The Agent must be able to signal "insufficient data" rather than hallucinating an answer.

---

### Instructions for the AI Assistant:

"Act as a Senior AI Architect. When writing code for this project:"

1. **Prioritize Modular Logic:** Separate the AI reasoning from the data processing.

2. **Always include a test file:** If you implement a new feature, provide the corresponding `pytest` file or `promptfoo` config.

3. **Keep it clean:** No hardcoded API keys or prompts.

4. **Enforce the Pipeline:** If the code doesn't fit the testing structure, suggest a refactor that makes it testable."

5. Always use a container first approach. Use docker and docker-compose if necessary.

6. Use `uv` for dependency management

---

### Claude specifics constraints

### 1. Advanced Tool Use (Agent Executor)

Claude is highly performant at **Parallel Tool Calling**. Unlike models that struggle with multi-step logic in a single turn, Claude can identify the need for both keyword expansion AND category filtering simultaneously.

- **Implementation:** In the `QueryArchitect` node, allow the model to bind multiple tools. It will generate a single JSON response containing all required tool calls, which the LangGraph executor can then run in parallel.
    
- **Result:** Reduced latency and more cohesive agent decision-making.
    

### 2. Prompt Caching (Operational Efficiency)

This is the "killer feature" for production economics. By caching static blocks of text (system instructions, Few-Shot examples, or search guidelines), you avoid re-processing the same tokens on every request.

- **Strategy:** Cache your `SummarizerTool` instructions and system prompts.
    
- **Impact:** When your `Synthesis Agent` processes 5+ abstracts, you are only paying for the _new_ content (the specific paper abstracts) rather than the entire instruction set. This can cut input token costs by up to 90% for high-volume operations.
    

### 3. Extended Thinking (Reasoning Layer)

With Claude 3.7 Sonnet’s "thinking" capabilities, you can shift from simple heuristic filtering to genuine qualitative analysis.

- **Application:** In the `QualityAgent`, move beyond simple BM25/FlashRank scores.
    
- **The Logic:** Use the "Thinking" mode to explicitly evaluate: _"Does the methodology in this paper directly answer the specific constraints of the user's query?"_
    
- **Outcome:** Drastic reduction in "relevance hallucinations" by forcing the model to articulate its justification _before_ assigning a final confidence score.

---
# Folder Structure

this is the app folder architecture.

arxiv-agent-crawler/
├── .github/workflows/          # CI/CD (Linting, Pytest, Promptfoo Evals)
├── docker/                     # Dockerfiles and docker-compose
│   ├── Dockerfile              # Production multi-stage build
│   └── docker-compose.yml      # Services (Crawler + LangFuse instance)
├── prompts/                    # Local cache/versioning for LangFuse prompts
├── src/                        # Core Application Code
│   ├── agents/                 # LangGraph nodes (The "Brain")
│   │   ├── architect.py        # Query Architect
│   │   ├── searcher.py         # Search Agent (API fetcher)
│   │   ├── quality.py          # Quality Agent (FlashRank/Filtering)
│   │   └── synthesizer.py      # Synthesis Agent
│   ├── core/                   # Search Engine Engine (Deterministic)
│   │   ├── engine.py           # RRF, BM25, FAISS logic
│   │   ├── embedding.py        # SentenceTransformers wrapper
│   │   └── reranker.py         # FlashRank wrapper
│   ├── api/                    # FastAPI endpoints
│   ├── utils/                  # Tenacity, Logger, LangFuse Callbacks
│   └── main.py                 # LangGraph Graph Definition
├── tests/
│   ├── unit/                   # Pytest: deterministic logic tests
│   ├── evals/                  # Promptfoo: Semantic/Intent evals
│   │   └── golden_dataset.json
│   └── conftest.py             # Mocking setup (arXiv, LiteLLM)
├── .env.example                # Template for API keys
├── pyproject.toml              # `uv` managed dependencies
└── README.md

# Instruction

1. **Environment Setup**: We'll create the `pyproject.toml` (using `uv`) and the `docker-compose.yml` to define your stack.
    
2. **The "Engine" First**: I recommend implementing `src/core/engine.py` first. Since this is deterministic math (BM25 + RRF), we can write the unit tests _before_ writing the code (True TDD).
    
3. **Observability Setup**: We'll define the LangFuse callback hook early so _every_ piece of code you write from day one is already instrumented.