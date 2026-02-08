"""
API Key Authentication Middleware.

Validates the Bearer token in the Authorization header against stored API keys.
In development mode, accepts a configurable bypass key.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import get_settings
from backend.utils.security import hash_api_key, verify_api_key

logger = logging.getLogger(__name__)

# ── In-memory key store (replace with DB in production) ───────────────────────

# Structure: { hashed_key: { org_id, key_id, name, scopes, ... } }
_api_keys: dict[str, dict] = {}

# Development bypass key
DEV_KEY = "tm_dev_key_for_local_testing_only"
DEV_ORG = "org_dev"
DEV_KEY_ID = "key_dev"


def register_api_key(
    raw_key: str,
    org_id: str,
    key_id: str,
    name: str = "default",
    scopes: list[str] | None = None,
) -> str:
    """Register an API key.  Returns the hashed key."""
    hashed = hash_api_key(raw_key)
    _api_keys[hashed] = {
        "org_id": org_id,
        "key_id": key_id,
        "name": name,
        "scopes": scopes or ["proxy", "dashboard"],
    }
    return hashed


def _lookup_key(raw_key: str) -> Optional[dict]:
    """Look up key metadata by raw key."""
    settings = get_settings()

    # Dev bypass
    if settings.environment == "development" and raw_key == DEV_KEY:
        return {"org_id": DEV_ORG, "key_id": DEV_KEY_ID, "name": "dev", "scopes": ["proxy", "dashboard", "admin"]}

    hashed = hash_api_key(raw_key)
    return _api_keys.get(hashed)


# ── Public paths that skip auth ──────────────────────────────────────────────

PUBLIC_PATHS = {
    "/",
    "/health",
    "/healthz",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates API keys for all non-public endpoints."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Missing or invalid Authorization header. Expected: Bearer <api_key>",
                        "type": "authentication_error",
                        "code": "invalid_api_key",
                    }
                },
            )

        raw_key = auth_header[7:]  # Strip "Bearer "
        key_meta = _lookup_key(raw_key)

        if not key_meta:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "message": "Invalid API key",
                        "type": "authentication_error",
                        "code": "invalid_api_key",
                    }
                },
            )

        # Attach org and key info to request state
        request.state.org_id = key_meta["org_id"]
        request.state.api_key_id = key_meta["key_id"]
        request.state.api_key_name = key_meta["name"]
        request.state.scopes = key_meta["scopes"]

        return await call_next(request)
