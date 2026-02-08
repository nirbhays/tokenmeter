"""
Health check endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.config import get_settings
from backend.services.provider_registry import get_provider_registry
from backend.services.usage_tracker import get_usage_tracker

router = APIRouter(tags=["Health"])


@router.get("/health")
@router.get("/healthz")
async def health():
    """Basic health check."""
    settings = get_settings()
    tracker = get_usage_tracker()
    registry = get_provider_registry()

    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "providers": len(registry.list_providers()),
        "models": len(registry.list_available_models()),
        "tracker": tracker.stats,
    }
