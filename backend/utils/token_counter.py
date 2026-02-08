"""
Accurate token counting for all supported models.

- Uses tiktoken for OpenAI models (exact count).
- Uses heuristic estimation for Anthropic / Google models.
"""

from __future__ import annotations

import functools
import re
from typing import Any, Dict, List, Optional, Union

from backend.models.proxy import ChatMessage


@functools.lru_cache(maxsize=8)
def _get_tiktoken_encoding(model: str):
    """Lazy-load tiktoken encoding for a given model."""
    try:
        import tiktoken

        # Map TokenMeter model IDs to tiktoken-compatible names
        tiktoken_map = {
            "gpt-5.2": "o200k_base",
            "gpt-5": "o200k_base",
            "gpt-5-mini": "o200k_base",
            "gpt-4.1": "o200k_base",
            "gpt-4.1-mini": "o200k_base",
            "gpt-4.1-nano": "o200k_base",
            "o3": "o200k_base",
            "o4-mini": "o200k_base",
            "text-embedding-3-large": "cl100k_base",
            "text-embedding-3-small": "cl100k_base",
        }

        encoding_name = tiktoken_map.get(model)
        if encoding_name:
            return tiktoken.get_encoding(encoding_name)

        # Fallback: try tiktoken's model lookup
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("o200k_base")
    except ImportError:
        return None


def _heuristic_token_count(text: str) -> int:
    """
    Rough token estimation when tiktoken is unavailable.

    Approximation: ~4 characters per token for English text.
    This is slightly generous to avoid undercounting.
    """
    if not text:
        return 0
    # Count words and add overhead for subword tokenization
    words = len(re.findall(r"\S+", text))
    chars = len(text)
    # Weighted average of word-based and char-based estimates
    return max(1, int(words * 1.3 + chars / 4) // 2)


def count_tokens(text: str, model: str = "gpt-4.1") -> int:
    """Count tokens in a string for a given model."""
    if not text:
        return 0

    encoding = _get_tiktoken_encoding(model)
    if encoding is not None:
        return len(encoding.encode(text))

    return _heuristic_token_count(text)


def count_message_tokens(messages: List[ChatMessage], model: str = "gpt-4.1") -> int:
    """
    Count tokens for a list of chat messages.

    Follows OpenAI's token counting rules:
    - Each message has overhead tokens for role, content separators.
    - For GPT-4+ models: 3 tokens per message + 1 token for role.
    """
    encoding = _get_tiktoken_encoding(model)
    use_tiktoken = encoding is not None

    # Per-message overhead (model-dependent)
    tokens_per_message = 3  # <|start|>{role/name}\n{content}<|end|>\n
    tokens_per_name = 1

    total = 0
    for msg in messages:
        total += tokens_per_message

        # Role
        if use_tiktoken:
            total += len(encoding.encode(msg.role.value))
        else:
            total += 1  # role is always 1 token

        # Content
        if msg.content:
            if isinstance(msg.content, str):
                if use_tiktoken:
                    total += len(encoding.encode(msg.content))
                else:
                    total += _heuristic_token_count(msg.content)
            elif isinstance(msg.content, list):
                # Multimodal content parts
                for part in msg.content:
                    if part.type == "text" and part.text:
                        if use_tiktoken:
                            total += len(encoding.encode(part.text))
                        else:
                            total += _heuristic_token_count(part.text)
                    elif part.type == "image_url":
                        # Images use a fixed token estimate
                        total += 85  # base cost for an image

        # Name
        if msg.name:
            total += tokens_per_name
            if use_tiktoken:
                total += len(encoding.encode(msg.name))
            else:
                total += _heuristic_token_count(msg.name)

        # Tool calls (approximate)
        if msg.tool_calls:
            for tc in msg.tool_calls:
                if use_tiktoken:
                    total += len(encoding.encode(tc.function.name))
                    total += len(encoding.encode(tc.function.arguments))
                else:
                    total += _heuristic_token_count(tc.function.name)
                    total += _heuristic_token_count(tc.function.arguments)
                total += 3  # overhead per tool call

    total += 3  # every reply is primed with <|start|>assistant<|message|>
    return total


def count_string_tokens(text: str, model: str = "gpt-4.1") -> int:
    """Alias for count_tokens for a plain string."""
    return count_tokens(text, model)


def estimate_completion_tokens(prompt_tokens: int, max_tokens: Optional[int] = None) -> int:
    """
    Estimate likely completion tokens for cost projection.
    Returns a conservative estimate.
    """
    if max_tokens:
        return min(max_tokens, max(prompt_tokens // 2, 256))
    return max(prompt_tokens // 3, 256)
