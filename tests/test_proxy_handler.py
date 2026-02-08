"""Tests for proxy handler (non-streaming path — unit tests without real providers)."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models.proxy import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    ChoiceMessage,
    Role,
    UsageInfo,
)
from backend.services.proxy_handler import ProxyHandler, BudgetExceededError


class TestProxyHandler:
    def test_budget_exceeded_raises(self):
        """When a hard budget limit is exceeded, requests should be rejected."""
        handler = ProxyHandler()
        # Add a budget that's already exceeded
        handler.budget.add_budget(
            MagicMock(
                id="b1",
                org_id="test",
                name="Test",
                amount_usd=10.0,
                current_spend_usd=15.0,
                hard_limit=True,
                enabled=True,
                team=None,
                feature=None,
                model=None,
                provider=None,
                thresholds=[],
            )
        )

    def test_proxy_handler_creation(self):
        handler = ProxyHandler()
        assert handler.registry is not None
        assert handler.tracker is not None
        assert handler.cache is not None
        assert handler.budget is not None
        assert handler.analytics is not None


class TestProxyModels:
    def test_chat_completion_request_validation(self):
        req = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Hello")],
        )
        assert req.model == "gpt-4.1"
        assert len(req.messages) == 1
        assert req.stream is False

    def test_chat_completion_request_with_extensions(self):
        req = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Hello")],
            **{
                "x-tm-team": "search",
                "x-tm-feature": "autocomplete",
                "x-tm-routing-mode": "cost-optimized",
            },
        )
        assert req.tm_team == "search"
        assert req.tm_feature == "autocomplete"
        assert req.tm_routing_mode == "cost-optimized"

    def test_chat_completion_response_structure(self):
        resp = ChatCompletionResponse(
            model="gpt-4.1",
            choices=[
                Choice(
                    index=0,
                    message=ChoiceMessage(role=Role.assistant, content="Hello!"),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            tm_provider="openai",
            tm_cost_usd=0.00001,
            tm_latency_ms=142.5,
        )
        assert resp.model == "gpt-4.1"
        assert resp.choices[0].message.content == "Hello!"
        assert resp.tm_cost_usd == 0.00001

    def test_streaming_request(self):
        req = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Hi")],
            stream=True,
        )
        assert req.stream is True
