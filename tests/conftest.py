import pytest

from src.core.engine import Document


@pytest.fixture
def sample_documents():
    """A small set of documents for testing the retrieval engine."""
    return [
        Document(
            doc_id="2401.00001",
            title="Autonomous Agents for CI/CD Pipeline Testing",
            abstract=(
                "We present a framework for deploying autonomous LLM-based agents "
                "to automate testing in continuous integration and continuous deployment "
                "pipelines. Our approach uses multi-agent collaboration to identify "
                "flaky tests and generate targeted test cases."
            ),
        ),
        Document(
            doc_id="2401.00002",
            title="A Survey on Retrieval-Augmented Generation",
            abstract=(
                "Retrieval-augmented generation (RAG) has emerged as a dominant paradigm "
                "for grounding large language models in external knowledge. This survey "
                "covers dense retrieval, sparse retrieval, and hybrid approaches."
            ),
        ),
        Document(
            doc_id="2401.00003",
            title="Neural Architecture Search with Reinforcement Learning",
            abstract=(
                "We propose a reinforcement learning controller that discovers novel "
                "neural architectures. The controller uses recurrent networks to sample "
                "candidate architectures and is trained with policy gradient methods."
            ),
        ),
        Document(
            doc_id="2401.00004",
            title="Multi-Agent Systems for Software Engineering",
            abstract=(
                "This paper explores the use of multiple LLM agents working together "
                "to solve complex software engineering tasks including code review, "
                "debugging, and automated testing in CI/CD environments."
            ),
        ),
        Document(
            doc_id="2401.00005",
            title="Efficient Transformers: A Comprehensive Survey",
            abstract=(
                "Transformer models have achieved state-of-the-art results across NLP tasks. "
                "This survey covers efficient transformer variants including sparse attention, "
                "linear attention, and low-rank factorization approaches."
            ),
        ),
    ]


@pytest.fixture
def agent_query():
    """A user query about agents in CI/CD."""
    return "How are autonomous agents being used to automate testing in CI/CD pipelines?"
