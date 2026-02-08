"""
Smart Routing Engine — decides which model/provider to use for each request.

Supports three routing modes:
  - cost-optimized:    route to cheapest model that can handle the complexity
  - latency-optimized: route to fastest model that meets quality threshold
  - quality-optimized: route to highest-quality model within budget

Also supports custom routing rules defined by the user.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.models.proxy import ChatCompletionRequest
from backend.models.provider import ModelCapability, ModelInfo, ProviderName
from backend.models.routing import (
    ComplexityLevel,
    RoutingConfig,
    RoutingDecision,
    RoutingMode,
    RoutingRule,
)
from backend.providers.pricing import ALL_MODELS, MODEL_BY_ID, get_model_info
from backend.services.request_classifier import RequestClassifier

logger = logging.getLogger(__name__)

# ── Default routing tables ────────────────────────────────────────────────────

# Cost-optimized: map complexity → model
COST_OPTIMIZED_MAP: Dict[ComplexityLevel, list[str]] = {
    ComplexityLevel.simple: ["gpt-4.1-nano", "gemini-2.5-flash", "claude-haiku-3.5"],
    ComplexityLevel.medium: ["gpt-4.1-mini", "gpt-4.1", "claude-sonnet-4.5"],
    ComplexityLevel.complex: ["gpt-4.1", "gpt-5", "claude-sonnet-4.5", "gemini-2.5-pro"],
}

LATENCY_OPTIMIZED_MAP: Dict[ComplexityLevel, list[str]] = {
    ComplexityLevel.simple: ["gpt-4.1-nano", "gemini-2.5-flash"],
    ComplexityLevel.medium: ["gpt-4.1-mini", "gemini-2.5-flash", "claude-haiku-3.5"],
    ComplexityLevel.complex: ["gpt-4.1", "gpt-5-mini", "claude-sonnet-4.5"],
}

QUALITY_OPTIMIZED_MAP: Dict[ComplexityLevel, list[str]] = {
    ComplexityLevel.simple: ["gpt-4.1-mini", "claude-sonnet-4.5"],
    ComplexityLevel.medium: ["gpt-5", "claude-sonnet-4.5", "gemini-2.5-pro"],
    ComplexityLevel.complex: ["gpt-5.2", "claude-opus-4", "o3"],
}


class RoutingEngine:
    """Evaluates routing rules and classification to pick the best model."""

    def __init__(self, available_models: Optional[list[str]] = None):
        """
        Args:
            available_models: List of model IDs that are currently available
                              (provider configured + API key set).  If None,
                              all known models are considered available.
        """
        self._available = set(available_models) if available_models else set(MODEL_BY_ID.keys())
        self._classifier = RequestClassifier()

    def route(
        self,
        request: ChatCompletionRequest,
        config: Optional[RoutingConfig] = None,
        *,
        team: Optional[str] = None,
        feature: Optional[str] = None,
    ) -> RoutingDecision:
        """
        Determine the best model for a request.

        Steps:
          1. Check model aliases (simple override)
          2. Evaluate custom routing rules (priority order)
          3. Classify complexity
          4. Apply routing mode (cost/latency/quality optimized)
          5. Check availability and fall back if needed
        """
        original_model = request.model
        routing_mode = RoutingMode.cost_optimized

        if config:
            routing_mode = config.mode

        # Override mode from request header
        if request.tm_routing_mode:
            try:
                routing_mode = RoutingMode(request.tm_routing_mode)
            except ValueError:
                pass

        # Use team/feature from request extensions if not passed
        team = team or request.tm_team
        feature = feature or request.tm_feature

        # ── Step 1: Model aliases ─────────────────────────────────────
        if config and original_model in config.model_aliases:
            alias = config.model_aliases[original_model]
            if alias in self._available:
                return RoutingDecision(
                    original_model=original_model,
                    routed_model=alias,
                    provider=self._get_provider(alias),
                    reason=f"Model alias: {original_model} → {alias}",
                    was_rerouted=True,
                )

        # ── Step 2: Custom rules ──────────────────────────────────────
        if config and config.rules:
            complexity, score = self._classifier.classify(request)
            sorted_rules = sorted(config.rules, key=lambda r: r.priority, reverse=True)

            for rule in sorted_rules:
                if not rule.enabled:
                    continue
                if self._rule_matches(rule, original_model, complexity, team, feature):
                    target = rule.target_model
                    if target in self._available:
                        return RoutingDecision(
                            original_model=original_model,
                            routed_model=target,
                            provider=self._get_provider(target),
                            reason=f"Custom rule: {rule.name}",
                            rule_id=rule.id,
                            complexity=complexity,
                            complexity_score=score,
                            was_rerouted=(target != original_model),
                        )

        # ── Step 3: If requested model is available, check if routing applies
        if not config or not config.enabled:
            # Routing disabled — pass through
            if original_model in self._available:
                return RoutingDecision(
                    original_model=original_model,
                    routed_model=original_model,
                    provider=self._get_provider(original_model),
                    reason="Routing disabled — direct pass-through",
                    was_rerouted=False,
                )

        # ── Step 4: Classify and apply routing mode ───────────────────
        complexity, score = self._classifier.classify(request)
        candidates = self._get_candidates(routing_mode, complexity)

        # Try each candidate in order
        for model_id in candidates:
            if model_id in self._available:
                return RoutingDecision(
                    original_model=original_model,
                    routed_model=model_id,
                    provider=self._get_provider(model_id),
                    reason=f"{routing_mode.value} routing: complexity={complexity.value} (score={score})",
                    complexity=complexity,
                    complexity_score=score,
                    was_rerouted=(model_id != original_model),
                )

        # ── Step 5: Fallback to requested model ──────────────────────
        if original_model in self._available:
            return RoutingDecision(
                original_model=original_model,
                routed_model=original_model,
                provider=self._get_provider(original_model),
                reason="No routing candidates available — using requested model",
                complexity=complexity,
                complexity_score=score,
                was_rerouted=False,
            )

        # ── Step 6: Fallback chain from config ───────────────────────
        if config and original_model in config.fallback_models:
            for fb in config.fallback_models[original_model]:
                if fb in self._available:
                    return RoutingDecision(
                        original_model=original_model,
                        routed_model=fb,
                        provider=self._get_provider(fb),
                        reason=f"Fallback chain: {original_model} → {fb}",
                        was_rerouted=True,
                    )

        # ── Ultimate fallback: first available model ──────────────────
        if self._available:
            first = next(iter(self._available))
            return RoutingDecision(
                original_model=original_model,
                routed_model=first,
                provider=self._get_provider(first),
                reason=f"Ultimate fallback — no suitable model found, using {first}",
                was_rerouted=True,
            )

        raise ValueError(f"No available models to handle request for {original_model}")

    def _rule_matches(
        self,
        rule: RoutingRule,
        model: str,
        complexity: ComplexityLevel,
        team: Optional[str],
        feature: Optional[str],
    ) -> bool:
        """Check if a routing rule's conditions match the current request."""
        if rule.source_models and model not in rule.source_models:
            return False
        if rule.complexity_levels and complexity not in rule.complexity_levels:
            return False
        if rule.teams and (not team or team not in rule.teams):
            return False
        if rule.features and (not feature or feature not in rule.features):
            return False
        return True

    def _get_candidates(self, mode: RoutingMode, complexity: ComplexityLevel) -> list[str]:
        """Get ordered candidate models for a given mode and complexity."""
        if mode == RoutingMode.cost_optimized:
            return COST_OPTIMIZED_MAP.get(complexity, [])
        elif mode == RoutingMode.latency_optimized:
            return LATENCY_OPTIMIZED_MAP.get(complexity, [])
        elif mode == RoutingMode.quality_optimized:
            return QUALITY_OPTIMIZED_MAP.get(complexity, [])
        return []

    def _get_provider(self, model_id: str) -> str:
        """Get the provider name for a model."""
        info = get_model_info(model_id)
        return info.provider.value if info else "unknown"
