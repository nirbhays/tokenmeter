"""
TokenMeter Configuration Management

Centralizes all configuration via environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Core ──────────────────────────────────────────────────────────
    app_name: str = "TokenMeter"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", description="development | staging | production")
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # ── Database (PostgreSQL / Supabase) ──────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/tokenmeter",
        description="Async PostgreSQL connection string",
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # ── ClickHouse (time-series metrics) ──────────────────────────────
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 9000
    clickhouse_http_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "tokenmeter"

    # ── Redis (Upstash / local) ───────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_password: Optional[str] = None

    # ── Auth (Clerk) ──────────────────────────────────────────────────
    clerk_secret_key: Optional[str] = None
    clerk_publishable_key: Optional[str] = None
    clerk_webhook_secret: Optional[str] = None

    # ── Stripe Billing ────────────────────────────────────────────────
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id_free: Optional[str] = None
    stripe_price_id_pro: Optional[str] = None
    stripe_price_id_enterprise: Optional[str] = None

    # ── LLM Provider API Keys ─────────────────────────────────────────
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # ── Proxy Settings ────────────────────────────────────────────────
    proxy_timeout_seconds: int = 120
    proxy_max_retries: int = 2
    proxy_streaming_chunk_size: int = 1024

    # ── Rate Limiting ─────────────────────────────────────────────────
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 100_000

    # ── Budget Alerts ─────────────────────────────────────────────────
    budget_check_interval_seconds: int = 60
    default_monthly_budget_usd: float = 100.0

    # ── Alert Delivery ────────────────────────────────────────────────
    slack_webhook_url: Optional[str] = None
    alert_email_smtp_host: Optional[str] = None
    alert_email_smtp_port: int = 587
    alert_email_smtp_user: Optional[str] = None
    alert_email_smtp_password: Optional[str] = None
    alert_email_from: str = "alerts@tokenmeter.dev"

    # ── Cache ─────────────────────────────────────────────────────────
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    semantic_cache_enabled: bool = False
    semantic_cache_similarity_threshold: float = 0.95

    # ── Routing Engine ────────────────────────────────────────────────
    routing_default_mode: str = "cost-optimized"  # cost-optimized | latency-optimized | quality-optimized
    routing_complexity_model: str = "heuristic"  # heuristic | ml

    # ── Security ──────────────────────────────────────────────────────
    api_key_hash_algorithm: str = "sha256"
    cors_origins: list[str] = ["http://localhost:3000", "https://tokenmeter.dev"]
    zero_logging_mode: bool = False  # When True, request/response bodies are NOT stored

    # ── Frontend URL ──────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("routing_default_mode")
    @classmethod
    def validate_routing_mode(cls, v: str) -> str:
        allowed = {"cost-optimized", "latency-optimized", "quality-optimized"}
        if v not in allowed:
            raise ValueError(f"routing_default_mode must be one of {allowed}")
        return v

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
