"""
Base provider interface.

Every LLM provider implementation inherits from `BaseLLMProvider` and must
implement both blocking and streaming chat completion methods.
"""

from __future__ import annotations

import abc
from typing import Any, AsyncIterator, Dict, Optional

from backend.models.proxy import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)


class BaseLLMProvider(abc.ABC):
    """Abstract base class for LLM provider adapters."""

    name: str
    api_base_url: str

    def __init__(self, api_key: str, timeout: int = 120, max_retries: int = 2):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    @abc.abstractmethod
    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> ChatCompletionResponse:
        """Send a non-streaming chat completion request."""
        ...

    @abc.abstractmethod
    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Send a streaming chat completion request.  Yields chunks."""
        ...

    async def embeddings(
        self,
        request: EmbeddingRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> EmbeddingResponse:
        """Send an embedding request.  Not all providers support this."""
        raise NotImplementedError(f"{self.name} does not support embeddings")

    async def health_check(self) -> bool:
        """Check if the provider is reachable.  Default: always healthy."""
        return True

    def _strip_tm_fields(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Remove TokenMeter extension fields before forwarding to the provider."""
        return {k: v for k, v in body.items() if not k.startswith(("tm_", "x-tm-", "x_tm_"))}
