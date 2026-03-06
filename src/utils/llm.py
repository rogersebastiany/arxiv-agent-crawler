"""LiteLLM wrapper for LLM calls with observability."""

from __future__ import annotations

import os

import litellm
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_MODEL = os.getenv("LITELLM_MODEL", "gpt-4o-mini")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def llm_completion(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Call an LLM via LiteLLM with retry logic.

    Returns the response content as a string.
    """
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()
