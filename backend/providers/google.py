"""
Google Gemini provider adapter.

Translates OpenAI-compatible requests to the Gemini API format and back.
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

GEMINI_MODEL_MAP: Dict[str, str] = {
    "gemini-2.5-pro": "gemini-2.5-pro-preview-06-05",
    "gemini-2.5-flash": "gemini-2.5-flash-preview-05-20",
}


class GoogleProvider(BaseLLMProvider):
    name = "google"
    api_base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, timeout: int = 120, max_retries: int = 2):
        super().__init__(api_key, timeout, max_retries)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_base_url,
                headers={"Content-Type": "application/json"},
                timeout=httpx.Timeout(self.timeout, connect=10.0),
            )
        return self._client

    def _convert_messages(self, messages: List[ChatMessage]) -> tuple[Optional[str], List[Dict[str, Any]]]:
        system_instruction: Optional[str] = None
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role == Role.system:
                system_instruction = msg.content if isinstance(msg.content, str) else str(msg.content)
                continue
            role = "user" if msg.role in (Role.user, Role.tool) else "model"
            text = msg.content if isinstance(msg.content, str) else (str(msg.content) if msg.content else "")
            contents.append({"role": role, "parts": [{"text": text}]})

        return system_instruction, contents

    def _build_body(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        system_instruction, contents = self._convert_messages(request.messages)
        body: Dict[str, Any] = {"contents": contents}

        if system_instruction:
            body["system_instruction"] = {"parts": [{"text": system_instruction}]}

        gen_config: Dict[str, Any] = {}
        if request.temperature is not None:
            gen_config["temperature"] = request.temperature
        if request.top_p is not None:
            gen_config["topP"] = request.top_p
        if request.max_tokens or request.max_completion_tokens:
            gen_config["maxOutputTokens"] = request.max_tokens or request.max_completion_tokens
        if request.stop:
            gen_config["stopSequences"] = request.stop if isinstance(request.stop, list) else [request.stop]

        if gen_config:
            body["generationConfig"] = gen_config

        return body

    def _convert_response(self, data: Dict[str, Any], original_model: str) -> ChatCompletionResponse:
        candidates = data.get("candidates", [{}])
        first = candidates[0] if candidates else {}
        content = first.get("content", {})
        parts = content.get("parts", [])
        text = "".join(p.get("text", "") for p in parts)

        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)

        finish = FinishReason.stop
        finish_reason_str = first.get("finishReason", "STOP")
        if finish_reason_str == "MAX_TOKENS":
            finish = FinishReason.length

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model=original_model,
            choices=[
                Choice(
                    index=0,
                    message=ChoiceMessage(role=Role.assistant, content=text),
                    finish_reason=finish,
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

    async def chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> ChatCompletionResponse:
        client = await self._get_client()
        model_id = GEMINI_MODEL_MAP.get(request.model, request.model)
        body = self._build_body(request)
        url = f"/models/{model_id}:generateContent?key={self.api_key}"
        resp = await client.post(url, json=body, headers=headers or {})
        resp.raise_for_status()
        return self._convert_response(resp.json(), request.model)

    async def chat_completion_stream(
        self,
        request: ChatCompletionRequest,
        *,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        client = await self._get_client()
        model_id = GEMINI_MODEL_MAP.get(request.model, request.model)
        body = self._build_body(request)
        url = f"/models/{model_id}:streamGenerateContent?alt=sse&key={self.api_key}"
        chunk_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        sent_role = False
        async with client.stream("POST", url, json=body, headers=headers or {}) as resp:
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

                candidates = event.get("candidates", [])
                if not candidates:
                    continue
                first = candidates[0]
                parts = first.get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)

                if not sent_role:
                    yield ChatCompletionChunk(
                        id=chunk_id,
                        model=request.model,
                        choices=[StreamChoice(index=0, delta=DeltaMessage(role=Role.assistant, content=text))],
                    )
                    sent_role = True
                else:
                    finish_reason = None
                    if first.get("finishReason") in ("STOP", "MAX_TOKENS"):
                        finish_reason = FinishReason.stop if first["finishReason"] == "STOP" else FinishReason.length

                    usage_meta = event.get("usageMetadata", {})
                    usage = None
                    if usage_meta:
                        usage = UsageInfo(
                            prompt_tokens=usage_meta.get("promptTokenCount", 0),
                            completion_tokens=usage_meta.get("candidatesTokenCount", 0),
                            total_tokens=usage_meta.get("promptTokenCount", 0) + usage_meta.get("candidatesTokenCount", 0),
                        )

                    yield ChatCompletionChunk(
                        id=chunk_id,
                        model=request.model,
                        choices=[StreamChoice(index=0, delta=DeltaMessage(content=text), finish_reason=finish_reason)],
                        usage=usage,
                    )

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get(f"/models?key={self.api_key}")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
