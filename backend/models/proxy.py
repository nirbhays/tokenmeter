"""
TokenMeter — Pydantic models for OpenAI-compatible proxy requests and responses.

These models ensure strict validation while remaining fully compatible with the
OpenAI API specification.  The proxy receives requests in this format and forwards
them (after routing) to the chosen LLM provider.
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────


class Role(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"
    function = "function"


class FinishReason(str, Enum):
    stop = "stop"
    length = "length"
    tool_calls = "tool_calls"
    content_filter = "content_filter"
    function_call = "function_call"


# ── Shared sub-models ─────────────────────────────────────────────────────────


class FunctionCall(BaseModel):
    name: str
    arguments: str


class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:24]}")
    type: Literal["function"] = "function"
    function: FunctionCall


class FunctionSpec(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ToolSpec(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionSpec


class ResponseFormat(BaseModel):
    type: Literal["text", "json_object", "json_schema"] = "text"
    json_schema: Optional[Dict[str, Any]] = None


# ── Chat Completion Request ───────────────────────────────────────────────────


class ContentPart(BaseModel):
    """Multimodal content part (text or image_url)."""
    type: Literal["text", "image_url"]
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None


class ChatMessage(BaseModel):
    role: Role
    content: Optional[Union[str, List[ContentPart]]] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    function_call: Optional[FunctionCall] = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible /v1/chat/completions request body."""

    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1, le=10)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    user: Optional[str] = None
    seed: Optional[int] = None
    tools: Optional[List[ToolSpec]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[ResponseFormat] = None

    # ── TokenMeter extensions (stripped before forwarding) ────────────
    tm_team: Optional[str] = Field(default=None, alias="x-tm-team", description="Team tag for cost attribution")
    tm_feature: Optional[str] = Field(default=None, alias="x-tm-feature", description="Feature tag for cost attribution")
    tm_routing_mode: Optional[str] = Field(default=None, alias="x-tm-routing-mode")
    tm_cache: Optional[bool] = Field(default=None, alias="x-tm-cache", description="Enable response caching")

    model_config = {"populate_by_name": True}


# ── Chat Completion Response ──────────────────────────────────────────────────


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChoiceMessage(BaseModel):
    role: Role = Role.assistant
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    function_call: Optional[FunctionCall] = None


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    finish_reason: Optional[FinishReason] = None
    logprobs: Optional[Any] = None


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible /v1/chat/completions response body."""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: Literal["chat.completion"] = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Choice]
    usage: Optional[UsageInfo] = None
    system_fingerprint: Optional[str] = None

    # TokenMeter additions
    tm_provider: Optional[str] = None
    tm_cost_usd: Optional[float] = None
    tm_latency_ms: Optional[float] = None
    tm_cached: Optional[bool] = None
    tm_routed_from: Optional[str] = None  # original requested model if rerouted


# ── Streaming (SSE) ──────────────────────────────────────────────────────────


class DeltaMessage(BaseModel):
    role: Optional[Role] = None
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    function_call: Optional[FunctionCall] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: DeltaMessage
    finish_reason: Optional[FinishReason] = None
    logprobs: Optional[Any] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk."""

    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[StreamChoice]
    usage: Optional[UsageInfo] = None
    system_fingerprint: Optional[str] = None


# ── Embeddings ────────────────────────────────────────────────────────────────


class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]
    encoding_format: Optional[Literal["float", "base64"]] = "float"
    dimensions: Optional[int] = None
    user: Optional[str] = None

    tm_team: Optional[str] = Field(default=None, alias="x-tm-team")
    tm_feature: Optional[str] = Field(default=None, alias="x-tm-feature")

    model_config = {"populate_by_name": True}


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: Union[List[float], str]
    index: int = 0


class EmbeddingResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[EmbeddingData]
    model: str
    usage: UsageInfo

    tm_provider: Optional[str] = None
    tm_cost_usd: Optional[float] = None
    tm_latency_ms: Optional[float] = None


# ── Legacy Completions ────────────────────────────────────────────────────────


class CompletionRequest(BaseModel):
    """Legacy /v1/completions endpoint."""
    model: str
    prompt: Union[str, List[str]]
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    user: Optional[str] = None

    tm_team: Optional[str] = Field(default=None, alias="x-tm-team")
    tm_feature: Optional[str] = Field(default=None, alias="x-tm-feature")

    model_config = {"populate_by_name": True}


class CompletionChoice(BaseModel):
    text: str
    index: int = 0
    logprobs: Optional[Any] = None
    finish_reason: Optional[FinishReason] = None


class CompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"cmpl-{uuid.uuid4().hex[:12]}")
    object: Literal["text_completion"] = "text_completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[CompletionChoice]
    usage: Optional[UsageInfo] = None
