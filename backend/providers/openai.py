"""
OpenAI provider adapter.

Handles communication with the OpenAI API for GPT-4.1, GPT-5, o3/o4-mini
and embedding models.  Supports both streaming and non-streaming modes.
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from backend.models.proxy import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    DeltaMessage,
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    StreamChoice,
    UsageInfo,
)
from backend.providers.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    name = "openai"
    api_base_url = "https://api.openai.com/v1"

    def __init__(self, api_key: str, timeout: int = 120, max_retries: int = 2):
        super().__init__(api_key, timeout, max_retries)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    def _build_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Build the JSON body to send to OpenAI, stripping TokenMeter fields."""
        body = request.model_dump(exclude_none=True, by_alias=False)
        return self._strip_tm_fields(body)

    # ── Non-streaming ─────────────────────────────────────────────────

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> ChatCompletionResponse:
        client = await self._get_client()
        body = self._build_body(request)
        body["stream"] = False

        extra_headers = headers or {}
        resp = await client.post("/chat/completions", json=body, headers=extra_headers)
        resp.raise_for_status()
        data = resp.json()
        return ChatCompletionResponse(**data)

    # ── Streaming ─────────────────────────────────────────────────────

    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        client = await self._get_client()
        body = self._build_body(request)
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}

        extra_headers = headers or {}
        async with client.stream(
            "POST", "/chat/completions", json=body, headers=extra_headers
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(payload)
                    yield ChatCompletionChunk(**chunk_data)
                except (json.JSONDecodeError, Exception):
                    continue

    # ── Embeddings ────────────────────────────────────────────────────

    async def embeddings(
        self,
        request: EmbeddingRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> EmbeddingResponse:
        client = await self._get_client()
        body = request.model_dump(exclude_none=True, by_alias=False)
        body = self._strip_tm_fields(body)

        extra_headers = headers or {}
        resp = await client.post("/embeddings", json=body, headers=extra_headers)
        resp.raise_for_status()
        data = resp.json()
        return EmbeddingResponse(**data)

    # ── Health ────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get("/models")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
