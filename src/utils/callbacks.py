"""LangFuse observability — configures LiteLLM's built-in callback integration."""

from __future__ import annotations

import os

import litellm


def configure_observability():
    """Enable LangFuse tracing for all LiteLLM calls if credentials are set.

    Call once at startup. Every litellm.completion() call will automatically
    be traced with input/output, latency, model, and token usage.
    """
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
