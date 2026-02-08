"""
Rate Limiting Middleware — Redis-backed sliding window rate limiter.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter using Redis.
    Falls back to permissive mode if Redis is unavailable.
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self._redis = redis_client

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit proxy endpoints
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        settings = get_settings()
        org_id = getattr(request.state, "org_id", "anonymous")
        key = f"tm:rl:{org_id}"

        if self._redis:
            try:
                now = time.time()
                window = 60  # 1 minute window
                limit = settings.rate_limit_requests_per_minute

                pipe = self._redis.pipeline()
                pipe.zremrangebyscore(key, 0, now - window)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, window)
                results = await pipe.execute()

                current_count = results[2]

                if current_count > limit:
                    retry_after = window
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "message": f"Rate limit exceeded. Limit: {limit} requests per minute.",
                                "type": "rate_limit_error",
                                "code": "rate_limit_exceeded",
                            }
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": str(max(0, limit - current_count)),
                            "X-RateLimit-Reset": str(int(now + window)),
                        },
                    )

                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(limit)
                response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count))
                return response

            except Exception as e:
                logger.warning("Rate limiter Redis error (permissive fallback): %s", e)

        # No Redis or error — permissive mode
        return await call_next(request)
