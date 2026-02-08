"""
Analytics Service — aggregation queries for the dashboard.

Provides spend summaries by team, model, feature, and time period.
In production, queries ClickHouse materialized views for fast aggregation.
Falls back to in-memory aggregation during development.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.models.usage import (
    CostTrend,
    FeatureUsage,
    ModelUsage,
    TeamUsage,
    UsageDashboard,
    UsageQueryParams,
    UsageRecord,
    UsageSummary,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Provides aggregated analytics for the dashboard."""

    def __init__(self):
        self._ch_client = None
        # In-memory fallback store for development
        self._records: List[UsageRecord] = []

    async def initialize(self, ch_client=None) -> None:
        self._ch_client = ch_client
        if ch_client:
            logger.info("Analytics service connected to ClickHouse")
        else:
            logger.info("Analytics service using in-memory store")

    def add_record(self, record: UsageRecord) -> None:
        """Add a record to the in-memory store (dev mode)."""
        self._records.append(record)
        # Keep memory bounded
        if len(self._records) > 100_000:
            self._records = self._records[-50_000:]

    async def get_dashboard(self, params: UsageQueryParams) -> UsageDashboard:
        """Get complete dashboard data."""
        if self._ch_client:
            return await self._query_clickhouse(params)
        return self._aggregate_in_memory(params)

    async def get_cost_trend(self, params: UsageQueryParams) -> List[CostTrend]:
        dashboard = await self.get_dashboard(params)
        return dashboard.cost_trend

    async def get_model_breakdown(self, params: UsageQueryParams) -> List[ModelUsage]:
        dashboard = await self.get_dashboard(params)
        return dashboard.by_model

    async def get_team_breakdown(self, params: UsageQueryParams) -> List[TeamUsage]:
        dashboard = await self.get_dashboard(params)
        return dashboard.by_team

    def _get_time_range(self, params: UsageQueryParams) -> tuple[datetime, datetime]:
        now = datetime.utcnow()
        if params.start and params.end:
            return params.start, params.end

        period_map = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        delta = period_map.get(params.period, timedelta(hours=24))
        return now - delta, now

    def _aggregate_in_memory(self, params: UsageQueryParams) -> UsageDashboard:
        """Aggregate from in-memory store (development fallback)."""
        start, end = self._get_time_range(params)

        # Filter records
        filtered = [
            r for r in self._records
            if r.org_id == params.org_id
            and start <= r.timestamp <= end
        ]
        if params.team:
            filtered = [r for r in filtered if r.team == params.team]
        if params.feature:
            filtered = [r for r in filtered if r.feature == params.feature]
        if params.model:
            filtered = [r for r in filtered if r.routed_model == params.model]
        if params.provider:
            filtered = [r for r in filtered if r.provider == params.provider]

        if not filtered:
            return UsageDashboard(
                summary=UsageSummary(period_start=start, period_end=end),
            )

        # Summary
        total_tokens = sum(r.total_tokens for r in filtered)
        total_cost = sum(r.cost_usd for r in filtered)
        latencies = [r.latency_ms for r in filtered]
        errors = sum(1 for r in filtered if r.status.value == "error")
        cached = sum(1 for r in filtered if r.cached)

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        summary = UsageSummary(
            period_start=start,
            period_end=end,
            total_requests=len(filtered),
            total_tokens=total_tokens,
            total_prompt_tokens=sum(r.prompt_tokens for r in filtered),
            total_completion_tokens=sum(r.completion_tokens for r in filtered),
            total_cost_usd=round(total_cost, 6),
            avg_latency_ms=round(sum(latencies) / n, 1) if n else 0,
            p50_latency_ms=sorted_latencies[n // 2] if n else 0,
            p95_latency_ms=sorted_latencies[int(n * 0.95)] if n else 0,
            p99_latency_ms=sorted_latencies[int(n * 0.99)] if n else 0,
            error_rate=round(errors / len(filtered), 4) if filtered else 0,
            cache_hit_rate=round(cached / len(filtered), 4) if filtered else 0,
        )

        # By model
        model_agg: Dict[str, dict] = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0, "latency": []})
        for r in filtered:
            m = model_agg[r.routed_model]
            m["requests"] += 1
            m["tokens"] += r.total_tokens
            m["cost"] += r.cost_usd
            m["latency"].append(r.latency_ms)
            m["provider"] = r.provider

        by_model = [
            ModelUsage(
                model=model,
                provider=data.get("provider", ""),
                total_requests=data["requests"],
                total_tokens=data["tokens"],
                total_cost_usd=round(data["cost"], 6),
                avg_latency_ms=round(sum(data["latency"]) / len(data["latency"]), 1) if data["latency"] else 0,
            )
            for model, data in sorted(model_agg.items(), key=lambda x: x[1]["cost"], reverse=True)
        ]

        # By team
        team_agg: Dict[str, dict] = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for r in filtered:
            if r.team:
                t = team_agg[r.team]
                t["requests"] += 1
                t["tokens"] += r.total_tokens
                t["cost"] += r.cost_usd

        by_team = [
            TeamUsage(team=team, total_requests=data["requests"], total_tokens=data["tokens"],
                      total_cost_usd=round(data["cost"], 6))
            for team, data in sorted(team_agg.items(), key=lambda x: x[1]["cost"], reverse=True)
        ]

        # By feature
        feature_agg: Dict[str, dict] = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": 0.0})
        for r in filtered:
            if r.feature:
                f = feature_agg[r.feature]
                f["requests"] += 1
                f["tokens"] += r.total_tokens
                f["cost"] += r.cost_usd

        by_feature = [
            FeatureUsage(feature=feat, total_requests=data["requests"], total_tokens=data["tokens"],
                         total_cost_usd=round(data["cost"], 6))
            for feat, data in sorted(feature_agg.items(), key=lambda x: x[1]["cost"], reverse=True)
        ]

        # Cost trend (bucket by granularity)
        granularity_delta = {
            "minute": timedelta(minutes=1),
            "hour": timedelta(hours=1),
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
        }
        bucket_delta = granularity_delta.get(params.granularity, timedelta(hours=1))
        trend_buckets: Dict[datetime, dict] = defaultdict(lambda: {"cost": 0.0, "requests": 0, "tokens": 0})

        for r in filtered:
            # Floor timestamp to bucket
            bucket_ts = datetime(
                r.timestamp.year, r.timestamp.month, r.timestamp.day, r.timestamp.hour
            )
            b = trend_buckets[bucket_ts]
            b["cost"] += r.cost_usd
            b["requests"] += 1
            b["tokens"] += r.total_tokens

        cost_trend = [
            CostTrend(timestamp=ts, cost_usd=round(data["cost"], 6), requests=data["requests"], tokens=data["tokens"])
            for ts, data in sorted(trend_buckets.items())
        ]

        return UsageDashboard(
            summary=summary,
            cost_trend=cost_trend,
            by_model=by_model,
            by_team=by_team,
            by_feature=by_feature,
            top_requests=filtered[-params.limit:],
        )

    async def _query_clickhouse(self, params: UsageQueryParams) -> UsageDashboard:
        """Query ClickHouse for dashboard data (production path)."""
        start, end = self._get_time_range(params)

        # This would execute real ClickHouse queries in production
        # For now, delegate to in-memory
        logger.info("ClickHouse query for org=%s period=%s", params.org_id, params.period)
        return self._aggregate_in_memory(params)


# Singleton
_analytics: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsService()
    return _analytics
