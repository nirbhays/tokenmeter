"""Tests for token counting."""

import pytest

from backend.utils.token_counter import (
    count_tokens,
    count_message_tokens,
    estimate_completion_tokens,
)
from backend.models.proxy import ChatMessage, Role


class TestTokenCounter:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        tokens = count_tokens("Hello, world!", model="gpt-4.1")
        # "Hello, world!" is typically 4 tokens
        assert 2 <= tokens <= 6

    def test_longer_text(self):
        text = "The quick brown fox jumps over the lazy dog. " * 10
        tokens = count_tokens(text, model="gpt-4.1")
        # ~100 tokens for 10 repetitions
        assert 80 <= tokens <= 120

    def test_message_tokens_single_message(self):
        messages = [ChatMessage(role=Role.user, content="Hello!")]
        tokens = count_message_tokens(messages, model="gpt-4.1")
        # "Hello!" ≈ 1-2 tokens + overhead
        assert tokens > 0

    def test_message_tokens_system_plus_user(self):
        messages = [
            ChatMessage(role=Role.system, content="You are a helpful assistant."),
            ChatMessage(role=Role.user, content="What is the capital of France?"),
        ]
        tokens = count_message_tokens(messages, model="gpt-4.1")
        assert tokens > 10

    def test_message_tokens_empty_content(self):
        messages = [ChatMessage(role=Role.user, content="")]
        tokens = count_message_tokens(messages, model="gpt-4.1")
        # Should still have overhead tokens
        assert tokens > 0

    def test_different_models(self):
        text = "Hello, how are you?"
        t1 = count_tokens(text, model="gpt-4.1")
        t2 = count_tokens(text, model="gpt-4.1-nano")
        # Both use o200k_base, should be same
        assert t1 == t2

    def test_estimate_completion(self):
        # With max_tokens
        est = estimate_completion_tokens(1000, max_tokens=500)
        assert est == 500

        # Without max_tokens — should return reasonable estimate
        est = estimate_completion_tokens(3000)
        assert est >= 256

    def test_code_tokens(self):
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        tokens = count_tokens(code, model="gpt-4.1")
        assert tokens > 10
