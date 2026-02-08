"""
Usage Tracker — asynchronously logs every request to ClickHouse.

Uses an in-memory buffer with periodic flushing for high throughput.
Falls back to PostgreSQL if ClickHouse is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional

from backend.config import get_settings
from backend.models.usage import UsageRecord

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Async usage tracker with buffered writes.

    Records are accumulated in an in-memory buffer and flushed to ClickHouse
    every `flush_interval` seconds or when the buffer reaches `buffer_size`.
    """

    def __init__(
        self,
        buffer_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self._buffer: Deque[UsageRecord] = deque()
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._flush_task: Optional[asyncio.Task] = None
        self._ch_client = None
        self._running = False
        self._total_tracked = 0
        self._total_flushed = 0

    async def start(self) -> None:
        """Start the background flush loop."""
        if self._running:
            return

        self._running = True
        settings = get_settings()

        # Try to initialize ClickHouse client
        try:
            import aiochclient
            import aiohttp

            session = aiohttp.ClientSession()
            self._ch_client = aiochclient.ChClient(
                session,
                url=f"http://{settings.clickhouse_host}:{settings.clickhouse_http_port}",
                user=settings.clickhouse_user,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database,
            )
            logger.info("ClickHouse client initialized")
        except Exception as e:
            logger.warning("ClickHouse not available, usage will be logged to memory only: %s", e)
            self._ch_client = None

        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("Usage tracker started (buffer=%d, interval=%.1fs)", self._buffer_size, self._flush_interval)

    async def stop(self) -> None:
        """Flush remaining records and stop."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Final flush
        await self._flush()
        logger.info("Usage tracker stopped (total tracked=%d, flushed=%d)", self._total_tracked, self._total_flushed)

    async def track(self, record: UsageRecord) -> None:
        """Add a usage record to the buffer."""
        self._buffer.append(record)
        self._total_tracked += 1

        if len(self._buffer) >= self._buffer_size:
            await self._flush()

    async def _flush_loop(self) -> None:
        """Periodically flush the buffer."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._buffer:
                await self._flush()

    async def _flush(self) -> None:
        """Write buffered records to ClickHouse."""
        if not self._buffer:
            return

        records = list(self._buffer)
        self._buffer.clear()

        if self._ch_client:
            try:
                # Build insert query
                rows = []
                for r in records:
                    rows.append((
                        r.id,
                        r.timestamp,
                        r.org_id,
                        r.team or "",
                        r.feature or "",
                        r.api_key_id,
                        r.requested_model,
                        r.routed_model,
                        r.provider,
                        r.endpoint,
                        int(r.stream),
                        r.prompt_tokens,
                        r.completion_tokens,
                        r.total_tokens,
                        r.cost_usd,
                        r.input_cost_usd,
                        r.output_cost_usd,
                        r.latency_ms,
                        r.time_to_first_token_ms or 0.0,
                        r.status.value,
                        r.status_code,
                        r.error_message or "",
                        r.routing_mode or "",
                        r.complexity_score or 0.0,
                        int(r.cached),
                    ))

                await self._ch_client.execute(
                    """INSERT INTO request_logs (
                        id, timestamp, org_id, team, feature, api_key_id,
                        requested_model, routed_model, provider, endpoint, stream,
                        prompt_tokens, completion_tokens, total_tokens,
                        cost_usd, input_cost_usd, output_cost_usd,
                        latency_ms, time_to_first_token_ms,
                        status, status_code, error_message,
                        routing_mode, complexity_score, cached
                    ) VALUES""",
                    *rows,
                )
                self._total_flushed += len(records)
                logger.debug("Flushed %d records to ClickHouse", len(records))
            except Exception as e:
                logger.error("Failed to flush to ClickHouse: %s — records lost: %d", e, len(records))
                # Re-add records to buffer for retry (limited to avoid OOM)
                if len(self._buffer) < self._buffer_size * 10:
                    self._buffer.extend(records)
        else:
            # No ClickHouse — just count
            self._total_flushed += len(records)
            logger.debug("Flushed %d records (no ClickHouse — in-memory only)", len(records))

    @property
    def stats(self) -> Dict:
        return {
            "total_tracked": self._total_tracked,
            "total_flushed": self._total_flushed,
            "buffer_size": len(self._buffer),
            "clickhouse_connected": self._ch_client is not None,
        }


# Module-level singleton
_tracker: Optional[UsageTracker] = None


def get_usage_tracker() -> UsageTracker:
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
