"""
Core Proxy Handler — the heart of TokenMeter.

Receives an incoming OpenAI-compatible request, routes it through the smart
router, forwards to the chosen LLM provider, tracks usage, calculates cost,
and returns the response.  Supports both streaming (SSE) and non-streaming modes.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import AsyncIterator, Optional

from backend.config import get_settings
from backend.models.proxy import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    UsageInfo,
)
from backend.models.routing import RoutingConfig, RoutingDecision
from backend.models.usage import RequestStatus, UsageRecord
from backend.services.alert_service import get_alert_service
from backend.services.analytics_service import get_analytics_service
from backend.services.budget_monitor import get_budget_monitor
from backend.services.cache_service import get_cache_service
from backend.services.cost_calculator import CostCalculator
from backend.services.provider_registry import get_provider_registry
from backend.services.routing_engine import RoutingEngine
from backend.services.usage_tracker import get_usage_tracker
from backend.utils.streaming import sse_generator, create_streaming_response
from backend.utils.token_counter import count_message_tokens

logger = logging.getLogger(__name__)


class ProxyHandler:
    """
    Handles the full lifecycle of a proxied LLM API request:

    1. Check cache
    2. Classify complexity + route
    3. Check budget hard limits
    4. Forward to provider (streaming or non-streaming)
    5. Calculate cost
    6. Track usage
    7. Record budget spend + trigger alerts
    8. Return response
    """

    def __init__(self):
        self.registry = get_provider_registry()
        self.tracker = get_usage_tracker()
        self.cache = get_cache_service()
        self.budget = get_budget_monitor()
        self.analytics = get_analytics_service()
        self.alerts = get_alert_service()
        self.cost_calc = CostCalculator()

    async def handle_chat_completion(
        self,
        request: ChatCompletionRequest,
        *,
        org_id: str,
        api_key_id: str,
        routing_config: Optional[RoutingConfig] = None,
    ) -> ChatCompletionResponse | AsyncIterator[str]:
        """
        Process a chat completion request.

        Returns:
            - ChatCompletionResponse for non-streaming requests
            - AsyncIterator[str] (SSE formatted) for streaming requests
        """
        start_time = time.perf_counter()
        team = request.tm_team
        feature = request.tm_feature

        # ── Step 1: Check budget hard limits ──────────────────────────
        exceeded = self.budget.check_hard_limit(org_id, team=team, feature=feature)
        if exceeded:
            raise BudgetExceededError(
                f"Budget '{exceeded.name}' exceeded: ${exceeded.current_spend_usd:.2f} / ${exceeded.amount_usd:.2f}"
            )

        # ── Step 2: Check cache (non-streaming only) ─────────────────
        if not request.stream:
            cached = await self.cache.get(request)
            if cached:
                latency = (time.perf_counter() - start_time) * 1000
                cached.tm_latency_ms = round(latency, 1)
                cached.tm_cached = True

                # Track cached request (still counts toward usage)
                await self._track_usage(
                    org_id=org_id,
                    api_key_id=api_key_id,
                    request=request,
                    decision=RoutingDecision(
                        original_model=request.model,
                        routed_model=request.model,
                        provider="cache",
                        reason="Cache hit",
                        was_rerouted=False,
                    ),
                    usage=cached.usage,
                    latency_ms=latency,
                    status=RequestStatus.cached,
                    cached=True,
                )
                return cached

        # ── Step 3: Route ─────────────────────────────────────────────
        available_models = [m.id for m in self.registry.list_available_models()]
        engine = RoutingEngine(available_models=available_models)
        decision = engine.route(request, routing_config, team=team, feature=feature)

        logger.info(
            "Routing: %s → %s (%s) [%s]",
            decision.original_model,
            decision.routed_model,
            decision.provider,
            decision.reason,
        )

        # ── Step 4: Get provider ──────────────────────────────────────
        provider = self.registry.get_provider_for_model(decision.routed_model)
        if not provider:
            raise ProviderUnavailableError(f"No provider available for model {decision.routed_model}")

        # Update model in request to the routed model
        routed_request = request.model_copy(update={"model": decision.routed_model})

        # ── Step 5: Forward request ───────────────────────────────────
        if request.stream:
            return self._handle_streaming(
                routed_request=routed_request,
                decision=decision,
                provider=provider,
                org_id=org_id,
                api_key_id=api_key_id,
                start_time=start_time,
            )
        else:
            return await self._handle_non_streaming(
                routed_request=routed_request,
                decision=decision,
                provider=provider,
                org_id=org_id,
                api_key_id=api_key_id,
                start_time=start_time,
            )

    async def _handle_non_streaming(
        self,
        routed_request: ChatCompletionRequest,
        decision: RoutingDecision,
        provider,
        org_id: str,
        api_key_id: str,
        start_time: float,
    ) -> ChatCompletionResponse:
        """Handle a non-streaming completion request."""
        try:
            response = await provider.chat_completion(routed_request)
            latency = (time.perf_counter() - start_time) * 1000

            # Enrich response with TokenMeter metadata
            response.tm_provider = decision.provider
            response.tm_latency_ms = round(latency, 1)
            if decision.was_rerouted:
                response.tm_routed_from = decision.original_model

            # Calculate cost
            usage = response.usage or UsageInfo()
            cost = self.cost_calc.calculate(
                decision.routed_model,
                usage.prompt_tokens,
                usage.completion_tokens,
            )
            response.tm_cost_usd = cost.total_cost_usd

            # Cache the response
            await self.cache.set(routed_request, response)

            # Track usage
            await self._track_usage(
                org_id=org_id,
                api_key_id=api_key_id,
                request=routed_request,
                decision=decision,
                usage=usage,
                latency_ms=latency,
                cost=cost,
            )

            return response

        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error("Proxy error: %s", e)
            await self._track_usage(
                org_id=org_id,
                api_key_id=api_key_id,
                request=routed_request,
                decision=decision,
                latency_ms=latency,
                status=RequestStatus.error,
                error_message=str(e),
            )
            raise

    async def _handle_streaming(
        self,
        routed_request: ChatCompletionRequest,
        decision: RoutingDecision,
        provider,
        org_id: str,
        api_key_id: str,
        start_time: float,
    ) -> AsyncIterator[str]:
        """Handle a streaming completion request.  Returns an SSE generator."""
        # Estimate prompt tokens before streaming (for cost tracking)
        prompt_tokens = count_message_tokens(routed_request.messages, routed_request.model)

        # Accumulators for streaming
        completion_tokens = 0
        first_token_time: Optional[float] = None
        final_usage: Optional[UsageInfo] = None

        async def on_chunk(chunk: ChatCompletionChunk):
            nonlocal completion_tokens, first_token_time, final_usage

            if first_token_time is None:
                first_token_time = time.perf_counter()

            # Count completion tokens from delta content
            for choice in chunk.choices:
                if choice.delta.content:
                    completion_tokens += 1  # Approximate: 1 chunk ≈ 1 token

            # Capture final usage if provider sends it
            if chunk.usage:
                final_usage = chunk.usage

        async def on_done():
            nonlocal final_usage
            latency = (time.perf_counter() - start_time) * 1000
            ttft = ((first_token_time - start_time) * 1000) if first_token_time else None

            # Use provider-reported usage if available, otherwise estimate
            if final_usage:
                usage = final_usage
            else:
                usage = UsageInfo(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )

            cost = self.cost_calc.calculate(
                decision.routed_model,
                usage.prompt_tokens,
                usage.completion_tokens,
            )

            await self._track_usage(
                org_id=org_id,
                api_key_id=api_key_id,
                request=routed_request,
                decision=decision,
                usage=usage,
                latency_ms=latency,
                ttft_ms=ttft,
                cost=cost,
                stream=True,
            )

        try:
            chunks = provider.chat_completion_stream(routed_request)
            return sse_generator(chunks, on_chunk=on_chunk, on_done=on_done)
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.error("Streaming proxy error: %s", e)
            await self._track_usage(
                org_id=org_id,
                api_key_id=api_key_id,
                request=routed_request,
                decision=decision,
                latency_ms=latency,
                status=RequestStatus.error,
                error_message=str(e),
                stream=True,
            )
            raise

    async def handle_embeddings(
        self,
        request: EmbeddingRequest,
        *,
        org_id: str,
        api_key_id: str,
    ) -> EmbeddingResponse:
        """Process an embedding request."""
        start_time = time.perf_counter()

        provider = self.registry.get_provider_for_model(request.model)
        if not provider:
            raise ProviderUnavailableError(f"No provider for model {request.model}")

        response = await provider.embeddings(request)
        latency = (time.perf_counter() - start_time) * 1000

        # Calculate cost
        usage = response.usage
        cost = self.cost_calc.calculate(
            request.model,
            usage.prompt_tokens,
            usage.completion_tokens,
        )
        response.tm_provider = provider.name
        response.tm_cost_usd = cost.total_cost_usd
        response.tm_latency_ms = round(latency, 1)

        return response

    async def _track_usage(
        self,
        *,
        org_id: str,
        api_key_id: str,
        request,
        decision: RoutingDecision,
        usage: Optional[UsageInfo] = None,
        latency_ms: float = 0,
        ttft_ms: Optional[float] = None,
        cost=None,
        status: RequestStatus = RequestStatus.success,
        error_message: Optional[str] = None,
        cached: bool = False,
        stream: bool = False,
    ):
        """Create and submit a usage record."""
        settings = get_settings()
        u = usage or UsageInfo()

        record = UsageRecord(
            org_id=org_id,
            team=getattr(request, "tm_team", None),
            feature=getattr(request, "tm_feature", None),
            api_key_id=api_key_id,
            requested_model=decision.original_model,
            routed_model=decision.routed_model,
            provider=decision.provider,
            endpoint="/v1/chat/completions",
            stream=stream,
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            total_tokens=u.total_tokens,
            cost_usd=cost.total_cost_usd if cost else 0.0,
            input_cost_usd=cost.input_cost_usd if cost else 0.0,
            output_cost_usd=cost.output_cost_usd if cost else 0.0,
            latency_ms=round(latency_ms, 1),
            time_to_first_token_ms=round(ttft_ms, 1) if ttft_ms else None,
            status=status,
            status_code=200 if status == RequestStatus.success else 500,
            error_message=error_message,
            routing_mode=decision.reason if decision else None,
            complexity_score=decision.complexity_score if decision else None,
            cached=cached,
        )

        # Track in usage tracker (async buffer → ClickHouse)
        await self.tracker.track(record)

        # Update analytics (in-memory for dev)
        self.analytics.add_record(record)

        # Update budget monitor
        if cost and cost.total_cost_usd > 0:
            alerts = self.budget.record_spend(
                org_id,
                cost.total_cost_usd,
                team=record.team,
                feature=record.feature,
                model=record.routed_model,
                provider=record.provider,
            )
            # Deliver any triggered alerts
            for alert in alerts:
                try:
                    await self.alerts.deliver(alert, alert.channels_notified)
                except Exception as e:
                    logger.error("Failed to deliver alert: %s", e)


class BudgetExceededError(Exception):
    """Raised when a hard budget limit is exceeded."""
    pass


class ProviderUnavailableError(Exception):
    """Raised when no provider is available for a model."""
    pass
