"""
TokenMeter — LLM API Cost Tracker & Smart Router

FastAPI application entry point with lifespan events.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.middleware.auth import AuthMiddleware
from backend.middleware.logging import LoggingMiddleware
from backend.middleware.rate_limiter import RateLimiterMiddleware

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("tokenmeter")


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()
    logger.info("Starting TokenMeter %s (%s)", settings.app_version, settings.environment)

    # Initialize provider registry
    from backend.services.provider_registry import get_provider_registry

    registry = get_provider_registry()
    await registry.initialize()

    # Initialize usage tracker
    from backend.services.usage_tracker import get_usage_tracker

    tracker = get_usage_tracker()
    await tracker.start()

    # Initialize cache
    from backend.services.cache_service import get_cache_service

    cache = get_cache_service()
    await cache.initialize()

    # Initialize budget monitor
    from backend.services.budget_monitor import get_budget_monitor

    budget = get_budget_monitor()
    await budget.start()

    # Initialize billing
    from backend.services.billing_service import get_billing_service

    billing = get_billing_service()
    await billing.initialize()

    # Initialize analytics
    from backend.services.analytics_service import get_analytics_service

    analytics = get_analytics_service()
    await analytics.initialize()

    logger.info(
        "TokenMeter ready — %d providers, %d models",
        len(registry.list_providers()),
        len(registry.list_available_models()),
    )

    yield

    # Shutdown
    logger.info("Shutting down TokenMeter...")
    await tracker.stop()
    await budget.stop()
    await cache.close()
    await registry.shutdown()
    logger.info("TokenMeter shut down cleanly")


# ── Application ───────────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="TokenMeter",
        description="LLM API Cost Tracker & Smart Router — Know exactly what you spend on AI",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # ── Middleware (order matters: first added = outermost) ────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimiterMiddleware)
    app.add_middleware(AuthMiddleware)

    # ── Routes ────────────────────────────────────────────────────────
    from backend.api.proxy import router as proxy_router
    from backend.api.dashboard import router as dashboard_router
    from backend.api.budgets import router as budgets_router
    from backend.api.routing import router as routing_router
    from backend.api.keys import router as keys_router
    from backend.api.billing import router as billing_router
    from backend.api.health import router as health_router

    app.include_router(proxy_router)
    app.include_router(dashboard_router)
    app.include_router(budgets_router)
    app.include_router(routing_router)
    app.include_router(keys_router)
    app.include_router(billing_router)
    app.include_router(health_router)

    @app.get("/")
    async def root():
        return {
            "name": "TokenMeter",
            "version": settings.app_version,
            "description": "LLM API Cost Tracker & Smart Router",
            "docs": "/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
