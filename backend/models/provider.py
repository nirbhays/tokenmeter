"""LLM provider models."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderName(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    google = "google"


class ModelCapability(str, Enum):
    chat = "chat"
    completion = "completion"
    embedding = "embedding"
    vision = "vision"
    function_calling = "function_calling"
    json_mode = "json_mode"
    streaming = "streaming"


class ModelPricing(BaseModel):
    """Pricing per 1M tokens (input/output)."""

    input_per_1m_tokens: float = Field(description="USD per 1M input tokens")
    output_per_1m_tokens: float = Field(description="USD per 1M output tokens")
    cached_input_per_1m_tokens: Optional[float] = None


class ModelInfo(BaseModel):
    """Complete information about a supported model."""

    id: str  # e.g. "gpt-4.1"
    name: str  # human-readable name
    provider: ProviderName
    pricing: ModelPricing
    context_window: int
    max_output_tokens: Optional[int] = None
    capabilities: List[ModelCapability] = Field(default_factory=list)
    quality_score: float = Field(ge=0.0, le=1.0, description="Quality rating 0-1")
    speed_score: float = Field(ge=0.0, le=1.0, description="Speed rating 0-1 (higher = faster)")
    deprecated: bool = False
    description: Optional[str] = None


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: ProviderName
    display_name: str
    api_base_url: str
    api_key_env_var: str
    models: List[ModelInfo] = Field(default_factory=list)
    enabled: bool = True
    timeout_seconds: int = 120
    max_retries: int = 2


class ProviderHealth(BaseModel):
    """Real-time health status of a provider."""

    provider: ProviderName
    status: str = "healthy"  # healthy | degraded | down
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    last_check: Optional[str] = None
    active_models: int = 0
