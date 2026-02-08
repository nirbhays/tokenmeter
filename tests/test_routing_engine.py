"""Tests for the routing engine."""

import pytest

from backend.models.proxy import ChatCompletionRequest, ChatMessage, Role
from backend.models.routing import (
    ComplexityLevel,
    RoutingConfig,
    RoutingMode,
    RoutingRule,
)
from backend.services.routing_engine import RoutingEngine


@pytest.fixture
def all_models():
    return [
        "gpt-4.1-nano", "gpt-4.1-mini", "gpt-4.1", "gpt-5", "gpt-5.2",
        "claude-haiku-3.5", "claude-sonnet-4.5", "claude-opus-4",
        "gemini-2.5-flash", "gemini-2.5-pro",
    ]


class TestRoutingEngine:
    def test_cost_optimized_simple_routes_to_cheap(self, simple_request, all_models):
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(org_id="test", mode=RoutingMode.cost_optimized, enabled=True)
        decision = engine.route(simple_request, config)

        # Simple queries should go to cheap models
        assert decision.routed_model in ["gpt-4.1-nano", "gemini-2.5-flash", "claude-haiku-3.5"]
        assert decision.was_rerouted is True

    def test_quality_optimized_complex_routes_to_best(self, complex_request, all_models):
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(org_id="test", mode=RoutingMode.quality_optimized, enabled=True)
        decision = engine.route(complex_request, config)

        # Complex queries should go to best models
        assert decision.routed_model in ["gpt-5.2", "claude-opus-4", "o3"]

    def test_routing_disabled_passthrough(self, simple_request, all_models):
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(org_id="test", mode=RoutingMode.cost_optimized, enabled=False)
        decision = engine.route(simple_request, config)

        # Should pass through to requested model
        assert decision.routed_model == "gpt-4.1"
        assert decision.was_rerouted is False

    def test_model_alias(self, simple_request, all_models):
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(
            org_id="test",
            model_aliases={"gpt-4.1": "gpt-4.1-mini"},
        )
        decision = engine.route(simple_request, config)

        assert decision.routed_model == "gpt-4.1-mini"
        assert decision.was_rerouted is True
        assert "alias" in decision.reason.lower()

    def test_custom_rule_takes_priority(self, simple_request, all_models):
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(
            org_id="test",
            mode=RoutingMode.cost_optimized,
            enabled=True,
            rules=[
                RoutingRule(
                    id="rule1",
                    name="Force GPT-5 for all",
                    priority=100,
                    source_models=["gpt-4.1"],
                    target_model="gpt-5",
                ),
            ],
        )
        decision = engine.route(simple_request, config)

        assert decision.routed_model == "gpt-5"
        assert decision.rule_id == "rule1"

    def test_team_based_routing(self, all_models):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Hello")],
            **{"x-tm-team": "search"},
        )
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(
            org_id="test",
            enabled=True,
            rules=[
                RoutingRule(
                    id="search_rule",
                    name="Search → Flash",
                    priority=10,
                    teams=["search"],
                    target_model="gemini-2.5-flash",
                ),
            ],
        )
        decision = engine.route(request, config, team="search")

        assert decision.routed_model == "gemini-2.5-flash"

    def test_fallback_when_model_unavailable(self):
        request = ChatCompletionRequest(
            model="gpt-5.2",
            messages=[ChatMessage(role=Role.user, content="Hello")],
        )
        # Only cheap models available
        engine = RoutingEngine(available_models=["gpt-4.1-nano", "gpt-4.1-mini"])
        config = RoutingConfig(
            org_id="test",
            fallback_models={"gpt-5.2": ["gpt-4.1", "gpt-4.1-mini"]},
        )
        decision = engine.route(request, config)

        assert decision.routed_model == "gpt-4.1-mini"
        assert decision.was_rerouted is True

    def test_header_routing_mode_override(self, simple_request, all_models):
        simple_request.tm_routing_mode = "quality-optimized"
        engine = RoutingEngine(available_models=all_models)
        config = RoutingConfig(org_id="test", mode=RoutingMode.cost_optimized, enabled=True)
        decision = engine.route(simple_request, config)

        # Quality-optimized for simple should still be a decent model
        assert decision.routed_model in ["gpt-4.1-mini", "claude-sonnet-4.5"]
