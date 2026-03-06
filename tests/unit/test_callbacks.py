"""Tests for the observability configuration."""

from unittest.mock import patch

import litellm

from src.utils.callbacks import configure_observability


def test_configures_langfuse_when_key_present():
    with patch.dict("os.environ", {"LANGFUSE_PUBLIC_KEY": "pk-test"}):
        configure_observability()
        assert "langfuse" in litellm.success_callback
        assert "langfuse" in litellm.failure_callback
    # Clean up
    litellm.success_callback = []
    litellm.failure_callback = []


def test_does_not_configure_without_key():
    with patch.dict("os.environ", {}, clear=True):
        litellm.success_callback = []
        litellm.failure_callback = []
        configure_observability()
        assert "langfuse" not in litellm.success_callback
        assert "langfuse" not in litellm.failure_callback
