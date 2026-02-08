"""
Cache Service — response caching for identical requests.

Supports exact-match caching (hash of model + messages + params)
and optional semantic caching (embedding similarity).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from backend.config import get_settings
from backend.models.proxy import ChatCompletionRequest, ChatCompletionResponse

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-backed response cache."""

    def __init__(self):
        self._redis = None
        self._enabled = False

    async def initialize(self) -> None:
        settings = get_settings()
        if not settings.cache_enabled:
            logger.info("Cache disabled by configuration")
            return

        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            self._enabled = True
            logger.info("Cache service initialized (TTL=%ds)", settings.cache_ttl_seconds)
        except Exception as e:
            logger.warning("Redis not available, caching disabled: %s", e)
            self._redis = None
            self._enabled = False

    def _cache_key(self, request: ChatCompletionRequest) -> str:
        """Generate a deterministic cache key from the request."""
        # Build a canonical representation
        canonical = {
            "model": request.model,
            "messages": [
                {"role": m.role.value, "content": m.content}
                for m in request.messages
            ],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_tokens or request.max_completion_tokens,
            "tools": [t.model_dump() for t in request.tools] if request.tools else None,
        }
        # Remove None values
        canonical = {k: v for k, v in canonical.items() if v is not None}
        canonical_json = json.dumps(canonical, sort_keys=True)
        hash_val = hashlib.sha256(canonical_json.encode()).hexdigest()
        return f"tm:cache:{hash_val}"

    async def get(self, request: ChatCompletionRequest) -> Optional[ChatCompletionResponse]:
        """Check cache for a matching response."""
        if not self._enabled or not self._redis:
            return None

        # Don't cache streaming requests
        if request.stream:
            return None

        # Skip if caching explicitly disabled for this request
        if request.tm_cache is False:
            return None

        try:
            key = self._cache_key(request)
            cached = await self._redis.get(key)
            if cached:
                data = json.loads(cached)
                response = ChatCompletionResponse(**data)
                response.tm_cached = True
                logger.debug("Cache hit: %s", key[:20])
                return response
        except Exception as e:
            logger.debug("Cache lookup error: %s", e)

        return None

    async def set(self, request: ChatCompletionRequest, response: ChatCompletionResponse) -> None:
        """Store a response in the cache."""
        if not self._enabled or not self._redis:
            return

        if request.stream:
            return

        # Don't cache error responses or empty responses
        if not response.choices:
            return

        # Don't cache if temperature > 0 (non-deterministic) unless explicitly requested
        if (request.temperature is not None and request.temperature > 0) and request.tm_cache is not True:
            return

        try:
            settings = get_settings()
            key = self._cache_key(request)
            data = response.model_dump_json(exclude_none=True)
            await self._redis.setex(key, settings.cache_ttl_seconds, data)
            logger.debug("Cache set: %s (TTL=%ds)", key[:20], settings.cache_ttl_seconds)
        except Exception as e:
            logger.debug("Cache write error: %s", e)

    async def invalidate(self, pattern: str = "tm:cache:*") -> int:
        """Invalidate cache entries matching a pattern."""
        if not self._enabled or not self._redis:
            return 0
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            if keys:
                deleted = await self._redis.delete(*keys)
                logger.info("Invalidated %d cache entries", deleted)
                return deleted
        except Exception as e:
            logger.error("Cache invalidation error: %s", e)
        return 0

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._enabled or not self._redis:
            return {"enabled": False}
        try:
            info = await self._redis.info("stats")
            keyspace = await self._redis.info("keyspace")
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": keyspace,
            }
        except Exception:
            return {"enabled": True, "error": "stats unavailable"}

    async def close(self):
        if self._redis:
            await self._redis.close()


# Singleton
_cache: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
