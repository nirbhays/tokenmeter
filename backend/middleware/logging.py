"""
Request/Response Logging Middleware.

Logs every request with timing, status code, and key metadata.
Respects zero-logging mode for request/response body privacy.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.config import get_settings

logger = logging.getLogger("tokenmeter.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000

            org_id = getattr(request.state, "org_id", "-")
            logger.info(
                "%s %s %s %d %.1fms org=%s rid=%s",
                method,
                path,
                client,
                response.status_code,
                elapsed,
                org_id,
                request_id,
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed:.1f}ms"
            return response

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(
                "%s %s %s ERROR %.1fms rid=%s error=%s",
                method,
                path,
                client,
                elapsed,
                request_id,
                str(e),
            )
            raise
