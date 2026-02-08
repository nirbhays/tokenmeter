"""
Proxy API endpoints — OpenAI-compatible /v1/chat/completions, /v1/embeddings, /v1/completions.

These are the core endpoints that applications hit.  They accept requests in
OpenAI format, route through TokenMeter's smart router, forward to the actual
LLM provider, and return the response with cost metadata.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.models.proxy import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    EmbeddingRequest,
    EmbeddingResponse,
)
from backend.services.proxy_handler import (
    BudgetExceededError,
    ProviderUnavailableError,
    ProxyHandler,
)
from backend.utils.streaming import create_streaming_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Proxy"])

# Module-level handler instance (initialized in main.py lifespan)
_handler: Optional[ProxyHandler] = None


def get_handler() -> ProxyHandler:
    global _handler
    if _handler is None:
        _handler = ProxyHandler()
    return _handler


def set_handler(handler: ProxyHandler):
    global _handler
    _handler = handler


# ── Chat Completions ──────────────────────────────────────────────────────────


@router.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    x_tm_team: Optional[str] = Header(None),
    x_tm_feature: Optional[str] = Header(None),
    x_tm_routing_mode: Optional[str] = Header(None),
):
    """
    OpenAI-compatible chat completions endpoint.

    Supports streaming (SSE) and non-streaming modes.
    Pass TokenMeter headers for cost attribution:
    - X-TM-Team: team identifier for cost grouping
    - X-TM-Feature: feature identifier for cost grouping
    - X-TM-Routing-Mode: override routing mode (cost-optimized, latency-optimized, quality-optimized)
    """
    handler = get_handler()
    org_id = getattr(request.state, "org_id", "default")
    api_key_id = getattr(request.state, "api_key_id", "unknown")

    # Apply header overrides
    if x_tm_team and not body.tm_team:
        body.tm_team = x_tm_team
    if x_tm_feature and not body.tm_feature:
        body.tm_feature = x_tm_feature
    if x_tm_routing_mode and not body.tm_routing_mode:
        body.tm_routing_mode = x_tm_routing_mode

    try:
        result = await handler.handle_chat_completion(
            body,
            org_id=org_id,
            api_key_id=api_key_id,
        )

        if body.stream:
            # result is an async generator of SSE strings
            return create_streaming_response(result)
        else:
            # result is a ChatCompletionResponse
            return result

    except BudgetExceededError as e:
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "message": str(e),
                    "type": "budget_exceeded",
                    "code": "budget_exceeded",
                }
            },
        )
    except ProviderUnavailableError as e:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "message": str(e),
                    "type": "provider_unavailable",
                    "code": "provider_unavailable",
                }
            },
        )
    except Exception as e:
        logger.exception("Proxy error")
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": f"Upstream provider error: {str(e)}",
                    "type": "proxy_error",
                    "code": "proxy_error",
                }
            },
        )


# ── Embeddings ────────────────────────────────────────────────────────────────


@router.post("/v1/embeddings")
async def embeddings(
    body: EmbeddingRequest,
    request: Request,
):
    """OpenAI-compatible embeddings endpoint."""
    handler = get_handler()
    org_id = getattr(request.state, "org_id", "default")
    api_key_id = getattr(request.state, "api_key_id", "unknown")

    try:
        return await handler.handle_embeddings(
            body,
            org_id=org_id,
            api_key_id=api_key_id,
        )
    except Exception as e:
        logger.exception("Embedding error")
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": f"Upstream error: {str(e)}",
                    "type": "proxy_error",
                    "code": "proxy_error",
                }
            },
        )


# ── Models List ───────────────────────────────────────────────────────────────


@router.get("/v1/models")
async def list_models(request: Request):
    """List available models (OpenAI-compatible)."""
    from backend.services.provider_registry import get_provider_registry

    registry = get_provider_registry()
    models = registry.list_available_models()

    return {
        "object": "list",
        "data": [
            {
                "id": m.id,
                "object": "model",
                "created": 1700000000,
                "owned_by": m.provider.value,
                "permission": [],
                "root": m.id,
                "parent": None,
            }
            for m in models
        ],
    }
