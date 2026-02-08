"""
Dashboard API — usage statistics, cost breakdowns, trends.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, Request

from backend.models.usage import UsageDashboard, UsageQueryParams
from backend.services.analytics_service import get_analytics_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=UsageDashboard)
async def dashboard_overview(
    request: Request,
    period: str = Query("24h", description="Time period: 1h, 24h, 7d, 30d, 90d"),
    team: Optional[str] = Query(None),
    feature: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    granularity: str = Query("hour"),
):
    """Get complete dashboard overview with all analytics."""
    org_id = getattr(request.state, "org_id", "default")
    analytics = get_analytics_service()

    params = UsageQueryParams(
        org_id=org_id,
        period=period,
        team=team,
        feature=feature,
        model=model,
        provider=provider,
        granularity=granularity,
    )

    return await analytics.get_dashboard(params)


@router.get("/cost-trend")
async def cost_trend(
    request: Request,
    period: str = Query("7d"),
    granularity: str = Query("day"),
    team: Optional[str] = Query(None),
):
    """Get cost trend time-series data."""
    org_id = getattr(request.state, "org_id", "default")
    analytics = get_analytics_service()

    params = UsageQueryParams(
        org_id=org_id,
        period=period,
        granularity=granularity,
        team=team,
    )

    data = await analytics.get_cost_trend(params)
    return {"data": [d.model_dump() for d in data]}


@router.get("/model-breakdown")
async def model_breakdown(
    request: Request,
    period: str = Query("24h"),
    team: Optional[str] = Query(None),
):
    """Get cost breakdown by model."""
    org_id = getattr(request.state, "org_id", "default")
    analytics = get_analytics_service()

    params = UsageQueryParams(org_id=org_id, period=period, team=team)
    data = await analytics.get_model_breakdown(params)
    return {"data": [d.model_dump() for d in data]}


@router.get("/team-breakdown")
async def team_breakdown(
    request: Request,
    period: str = Query("30d"),
):
    """Get cost breakdown by team."""
    org_id = getattr(request.state, "org_id", "default")
    analytics = get_analytics_service()

    params = UsageQueryParams(org_id=org_id, period=period)
    data = await analytics.get_team_breakdown(params)
    return {"data": [d.model_dump() for d in data]}


@router.get("/providers")
async def provider_status(request: Request):
    """Get health status of all configured providers."""
    from backend.services.provider_registry import get_provider_registry

    registry = get_provider_registry()
    health = await registry.health_check_all()
    return {"data": [h.model_dump() for h in health]}
