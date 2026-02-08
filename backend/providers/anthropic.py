"""
Anthropic provider adapter.

Translates OpenAI-compatible requests to the Anthropic Messages API format
and translates responses back.  Supports streaming via SSE.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from backend.models.proxy import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    ChoiceMessage,
    DeltaMessage,
    FinishReason,
    Role,
    StreamChoice,
    UsageInfo,
)
from backend.providers.base import BaseLLMProvider


# ── Model ID mapping (OpenAI-style → Anthropic API model ID) ─────────────────

ANTHROPIC_MODEL_MAP: Dict[str, str] = {
    "claude-opus-4": "claude-opus-4-20250514",
    "claude-sonnet-4.5": "claude-sonnet-4-5-20250514",
    "claude-haiku-3.5": "claude-3-5-haiku-20241022",
}


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"
    api_base_url = "https://api.anthropic.com/v1"

    def __init__(self, api_key: str, timeout: int = 120, max_retries: int = 2):
        super().__init__(api_key, timeout, max_retries)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2024-10-22",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Split system message out (Anthropic uses a top-level `system` param)
        and convert remaining messages to Anthropic format.
        """
        system_prompt: Optional[str] = None
        converted: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role == Role.system:
                system_prompt = msg.content if isinstance(msg.content, str) else str(msg.content)
                continue

            role = "user" if msg.role in (Role.user, Role.tool) else "assistant"
            content = msg.content if isinstance(msg.content, str) else (str(msg.content) if msg.content else "")
            converted.append({"role": role, "content": content})

        return system_prompt, converted

    def _build_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Build an Anthropic Messages API request body."""
        model_id = ANTHROPIC_MODEL_MAP.get(request.model, request.model)
        system_prompt, messages = self._convert_messages(request.messages)

        body: Dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "max_tokens": request.max_tokens or request.max_completion_tokens or 4096,
        }

        if system_prompt:
            body["system"] = system_prompt
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.stop:
            body["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]

        return body

    def _convert_response(self, data: Dict[str, Any], original_model: str) -> ChatCompletionResponse:
        """Convert Anthropic response to OpenAI format."""
        content_blocks = data.get("content", [])
        text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
        full_text = "".join(text_parts)

        usage = data.get("usage", {})
        stop = data.get("stop_reason", "end_turn")
        finish = FinishReason.stop if stop in ("end_turn", "stop_sequence") else FinishReason.length

        return ChatCompletionResponse(
            id=f"chatcmpl-{data.get('id', uuid.uuid4().hex[:12])}",
            model=original_model,
            choices=[
                Choice(
                    index=0,
                    message=ChoiceMessage(role=Role.assistant, content=full_text),
                    finish_reason=finish,
                )
            ],
            usage=UsageInfo(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            ),
        )

    # ── Non-streaming ─────────────────────────────────────────────────

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> ChatCompletionResponse:
        client = await self._get_client()
        body = self._build_body(request)

        resp = await client.post("/messages", json=body, headers=headers or {})
        resp.raise_for_status()
        data = resp.json()
        return self._convert_response(data, request.model)

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

        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        input_tokens = 0
        output_tokens = 0

        async with client.stream("POST", "/messages", json=body, headers=headers or {}) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if not payload:
                    continue
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type", "")

                if event_type == "message_start":
                    usage = event.get("message", {}).get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    # Send initial chunk with role
                    yield ChatCompletionChunk(
                        id=chunk_id,
                        model=request.model,
                        choices=[StreamChoice(index=0, delta=DeltaMessage(role=Role.assistant))],
                    )

                elif event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        output_tokens += 1  # approximate; real count comes from message_delta
                        yield ChatCompletionChunk(
                            id=chunk_id,
                            model=request.model,
                            choices=[StreamChoice(index=0, delta=DeltaMessage(content=text))],
                        )

                elif event_type == "message_delta":
                    usage = event.get("usage", {})
                    output_tokens = usage.get("output_tokens", output_tokens)
                    stop = event.get("delta", {}).get("stop_reason", "end_turn")
                    finish = FinishReason.stop if stop in ("end_turn", "stop_sequence") else FinishReason.length
                    yield ChatCompletionChunk(
                        id=chunk_id,
                        model=request.model,
                        choices=[StreamChoice(index=0, delta=DeltaMessage(), finish_reason=finish)],
                        usage=UsageInfo(
                            prompt_tokens=input_tokens,
                            completion_tokens=output_tokens,
                            total_tokens=input_tokens + output_tokens,
                        ),
                    )

    # ── Health ────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            # Anthropic has no /models endpoint; send a tiny request
            resp = await client.post(
                "/messages",
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
            )
            return resp.status_code in (200, 429)  # 429 = healthy but rate-limited
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
