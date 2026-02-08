"""
TokenMeter Python SDK Client — drop-in OpenAI replacement.

Proxies all requests through TokenMeter for cost tracking, smart routing,
and budget management.  Supports streaming SSE.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, Iterator, List, Optional, Union

import httpx


# ── Response types ────────────────────────────────────────────────────────────


@dataclass
class Message:
    role: str = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None


@dataclass
class Choice:
    index: int = 0
    message: Optional[Message] = None
    delta: Optional[Message] = None
    finish_reason: Optional[str] = None


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatCompletion:
    """Non-streaming chat completion response."""
    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: List[Choice] = field(default_factory=list)
    usage: Optional[Usage] = None
    # TokenMeter extensions
    tm_provider: Optional[str] = None
    tm_cost_usd: Optional[float] = None
    tm_latency_ms: Optional[float] = None
    tm_cached: Optional[bool] = None
    tm_routed_from: Optional[str] = None


@dataclass
class ChatCompletionChunk:
    """Streaming chat completion chunk."""
    id: str = ""
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: List[Choice] = field(default_factory=list)
    usage: Optional[Usage] = None


class ChatCompletionStream:
    """Iterable wrapper around SSE streaming response."""

    def __init__(self, response: httpx.Response):
        self._response = response
        self._iterator = response.iter_lines()

    def __iter__(self):
        return self

    def __next__(self) -> ChatCompletionChunk:
        for line in self._iterator:
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                raise StopIteration
            try:
                data = json.loads(payload)
                choices = []
                for c in data.get("choices", []):
                    delta = c.get("delta", {})
                    choices.append(Choice(
                        index=c.get("index", 0),
                        delta=Message(
                            role=delta.get("role"),
                            content=delta.get("content"),
                        ),
                        finish_reason=c.get("finish_reason"),
                    ))
                usage = None
                if data.get("usage"):
                    u = data["usage"]
                    usage = Usage(
                        prompt_tokens=u.get("prompt_tokens", 0),
                        completion_tokens=u.get("completion_tokens", 0),
                        total_tokens=u.get("total_tokens", 0),
                    )
                return ChatCompletionChunk(
                    id=data.get("id", ""),
                    model=data.get("model", ""),
                    choices=choices,
                    usage=usage,
                )
            except (json.JSONDecodeError, KeyError):
                continue
        raise StopIteration

    def close(self):
        self._response.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── Chat Completions API ──────────────────────────────────────────────────────


class Completions:
    """chat.completions namespace."""

    def __init__(self, client: "TokenMeterClient"):
        self._client = client

    def create(
        self,
        *,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stream: Optional[bool] = False,
        stop: Optional[Union[str, List[str]]] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        seed: Optional[int] = None,
        # TokenMeter extensions
        tm_team: Optional[str] = None,
        tm_feature: Optional[str] = None,
        tm_routing_mode: Optional[str] = None,
        tm_cache: Optional[bool] = None,
        **kwargs,
    ) -> Union[ChatCompletion, ChatCompletionStream]:
        """Create a chat completion — compatible with openai.chat.completions.create()."""

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        # Optional params
        if temperature is not None: body["temperature"] = temperature
        if top_p is not None: body["top_p"] = top_p
        if n is not None: body["n"] = n
        if stream: body["stream"] = True
        if stop is not None: body["stop"] = stop
        if max_tokens is not None: body["max_tokens"] = max_tokens
        if max_completion_tokens is not None: body["max_completion_tokens"] = max_completion_tokens
        if tools is not None: body["tools"] = tools
        if tool_choice is not None: body["tool_choice"] = tool_choice
        if response_format is not None: body["response_format"] = response_format
        if user is not None: body["user"] = user
        if seed is not None: body["seed"] = seed

        # TokenMeter extensions (sent as body fields)
        if tm_team: body["x-tm-team"] = tm_team
        if tm_feature: body["x-tm-feature"] = tm_feature
        if tm_routing_mode: body["x-tm-routing-mode"] = tm_routing_mode
        if tm_cache is not None: body["x-tm-cache"] = tm_cache

        headers: Dict[str, str] = {}
        if tm_team: headers["X-TM-Team"] = tm_team
        if tm_feature: headers["X-TM-Feature"] = tm_feature
        if tm_routing_mode: headers["X-TM-Routing-Mode"] = tm_routing_mode

        if stream:
            return self._stream(body, headers)
        return self._non_stream(body, headers)

    def _non_stream(self, body: Dict[str, Any], headers: Dict[str, str]) -> ChatCompletion:
        resp = self._client._request("POST", "/v1/chat/completions", json=body, headers=headers)
        data = resp.json()

        choices = []
        for c in data.get("choices", []):
            msg = c.get("message", {})
            choices.append(Choice(
                index=c.get("index", 0),
                message=Message(
                    role=msg.get("role", "assistant"),
                    content=msg.get("content"),
                    tool_calls=msg.get("tool_calls"),
                ),
                finish_reason=c.get("finish_reason"),
            ))

        usage = None
        if data.get("usage"):
            u = data["usage"]
            usage = Usage(
                prompt_tokens=u.get("prompt_tokens", 0),
                completion_tokens=u.get("completion_tokens", 0),
                total_tokens=u.get("total_tokens", 0),
            )

        return ChatCompletion(
            id=data.get("id", ""),
            model=data.get("model", ""),
            created=data.get("created", 0),
            choices=choices,
            usage=usage,
            tm_provider=data.get("tm_provider"),
            tm_cost_usd=data.get("tm_cost_usd"),
            tm_latency_ms=data.get("tm_latency_ms"),
            tm_cached=data.get("tm_cached"),
            tm_routed_from=data.get("tm_routed_from"),
        )

    def _stream(self, body: Dict[str, Any], headers: Dict[str, str]) -> ChatCompletionStream:
        resp = self._client._request_stream("POST", "/v1/chat/completions", json=body, headers=headers)
        return ChatCompletionStream(resp)


# ── Chat namespace ────────────────────────────────────────────────────────────


class Chat:
    def __init__(self, client: "TokenMeterClient"):
        self.completions = Completions(client)


# ── Models namespace ──────────────────────────────────────────────────────────


class Models:
    def __init__(self, client: "TokenMeterClient"):
        self._client = client

    def list(self):
        resp = self._client._request("GET", "/v1/models")
        return resp.json()


# ── Main Client ───────────────────────────────────────────────────────────────


class TokenMeterClient:
    """
    Drop-in replacement for the OpenAI Python client.

    Usage:
        from tokenmeter import OpenAI

        client = OpenAI()
        # or
        client = OpenAI(api_key="tm_...", base_url="https://proxy.tokenmeter.dev")
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key or os.environ.get("TOKENMETER_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("TOKENMETER_BASE_URL") or "http://localhost:8000").rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "tokenmeter-python/0.1.0",
            },
            timeout=httpx.Timeout(self.timeout),
        )

        # API namespaces (OpenAI-compatible)
        self.chat = Chat(self)
        self.models = Models(self)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make a synchronous HTTP request."""
        extra_headers = kwargs.pop("headers", {})
        resp = self._client.request(method, path, headers=extra_headers, **kwargs)
        resp.raise_for_status()
        return resp

    def _request_stream(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make a streaming HTTP request."""
        extra_headers = kwargs.pop("headers", {})
        req = self._client.build_request(method, path, headers=extra_headers, **kwargs)
        resp = self._client.send(req, stream=True)
        resp.raise_for_status()
        return resp

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
