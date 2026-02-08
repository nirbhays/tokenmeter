"""Usage tracking models — records every LLM API call flowing through TokenMeter."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    success = "success"
    error = "error"
    timeout = "timeout"
    rate_limited = "rate_limited"
    cached = "cached"


class UsageRecord(BaseModel):
    """Single request log entry written to ClickHouse."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    org_id: str
    team: Optional[str] = None
    feature: Optional[str] = None
    api_key_id: str

    # Request details
    requested_model: str
    routed_model: str
    provider: str
    endpoint: str  # /v1/chat/completions, /v1/embeddings, etc.
    stream: bool = False

    # Tokens
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Cost
    cost_usd: float = 0.0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0

    # Performance
    latency_ms: float = 0.0
    time_to_first_token_ms: Optional[float] = None

    # Status
    status: RequestStatus = RequestStatus.success
    status_code: int = 200
    error_message: Optional[str] = None

    # Routing metadata
    routing_mode: Optional[str] = None
    complexity_score: Optional[float] = None
    cached: bool = False

    # Metadata (not stored in zero-logging mode)
    request_metadata: Optional[Dict[str, Any]] = None


class UsageSummary(BaseModel):
    """Aggregated usage stats for dashboard display."""

    period_start: datetime
    period_end: datetime
    total_requests: int = 0
    total_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0


class ModelUsage(BaseModel):
    """Per-model usage breakdown."""

    model: str
    provider: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0


class TeamUsage(BaseModel):
    """Per-team usage breakdown."""

    team: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0


class FeatureUsage(BaseModel):
    """Per-feature usage breakdown."""

    feature: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0


class CostTrend(BaseModel):
    """Time-series cost data point."""

    timestamp: datetime
    cost_usd: float
    requests: int
    tokens: int


class UsageDashboard(BaseModel):
    """Complete dashboard data payload."""

    summary: UsageSummary
    cost_trend: List[CostTrend] = []
    by_model: List[ModelUsage] = []
    by_team: List[TeamUsage] = []
    by_feature: List[FeatureUsage] = []
    top_requests: List[UsageRecord] = []


class UsageQueryParams(BaseModel):
    """Parameters for querying usage data."""

    org_id: str
    period: str = "24h"  # 1h, 24h, 7d, 30d, 90d, custom
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    team: Optional[str] = None
    feature: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    granularity: str = "hour"  # minute, hour, day, week, month
    limit: int = 100
    offset: int = 0
