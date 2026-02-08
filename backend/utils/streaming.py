"""
SSE streaming utilities for proxying LLM responses.

Handles formatting chunks as Server-Sent Events and managing streaming
connections between the client and upstream LLM providers.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict

from starlette.responses import StreamingResponse

from backend.models.proxy import ChatCompletionChunk


def format_sse(data: str) -> str:
    """Format a string as an SSE event."""
    return f"data: {data}\n\n"


def format_sse_done() -> str:
    """Format the SSE stream termination marker."""
    return "data: [DONE]\n\n"


def chunk_to_sse(chunk: ChatCompletionChunk) -> str:
    """Convert a ChatCompletionChunk to an SSE-formatted string."""
    return format_sse(chunk.model_dump_json(exclude_none=True))


async def sse_generator(
    chunks: AsyncIterator[ChatCompletionChunk],
    *,
    on_chunk: Any = None,
    on_done: Any = None,
) -> AsyncIterator[str]:
    """
    Wraps an async iterator of ChatCompletionChunk into SSE-formatted strings.

    Parameters:
        chunks: Async iterator of completion chunks from a provider.
        on_chunk: Optional async callback(chunk) called for each chunk (for tracking).
        on_done: Optional async callback() called when stream completes.
    """
    try:
        async for chunk in chunks:
            if on_chunk:
                await on_chunk(chunk)
            yield chunk_to_sse(chunk)
        yield format_sse_done()
    finally:
        if on_done:
            await on_done()


def create_streaming_response(
    generator: AsyncIterator[str],
    *,
    headers: Dict[str, str] | None = None,
) -> StreamingResponse:
    """Create a Starlette StreamingResponse for SSE."""
    default_headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable nginx buffering
    }
    if headers:
        default_headers.update(headers)

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=default_headers,
    )
