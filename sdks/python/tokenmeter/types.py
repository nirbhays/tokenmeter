"""Type definitions for the TokenMeter Python SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class TokenMeterUsage:
    """Extended usage info returned by TokenMeter."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0


@dataclass
class TokenMeterMetadata:
    """Metadata added by TokenMeter to every response."""
    provider: Optional[str] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None
    cached: Optional[bool] = None
    routed_from: Optional[str] = None
    routing_reason: Optional[str] = None
