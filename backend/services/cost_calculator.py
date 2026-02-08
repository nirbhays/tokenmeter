"""
Real-time cost calculation for LLM API requests.

Computes the dollar cost of a request based on the model used,
token counts, and the provider's pricing table.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.models.provider import ModelInfo, ModelPricing
from backend.providers.pricing import MODEL_BY_ID, get_model_info

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculates USD cost for a request given model + token counts."""

    @staticmethod
    def calculate(
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        *,
        cached_prompt_tokens: int = 0,
    ) -> CostBreakdown:
        """
        Calculate cost breakdown for a request.

        Args:
            model_id: The model used (e.g. "gpt-4.1")
            prompt_tokens: Number of input/prompt tokens
            completion_tokens: Number of output/completion tokens
            cached_prompt_tokens: Tokens served from prompt cache (cheaper rate)

        Returns:
            CostBreakdown with input, output, and total cost in USD
        """
        model = get_model_info(model_id)
        if not model:
            logger.warning("Unknown model '%s' — cost will be zero", model_id)
            return CostBreakdown(model_id=model_id)

        pricing = model.pricing

        # Separate cached vs non-cached input tokens
        non_cached_input = max(0, prompt_tokens - cached_prompt_tokens)

        input_cost = (non_cached_input / 1_000_000) * pricing.input_per_1m_tokens
        if cached_prompt_tokens > 0 and pricing.cached_input_per_1m_tokens is not None:
            input_cost += (cached_prompt_tokens / 1_000_000) * pricing.cached_input_per_1m_tokens

        output_cost = (completion_tokens / 1_000_000) * pricing.output_per_1m_tokens
        total_cost = input_cost + output_cost

        return CostBreakdown(
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_prompt_tokens=cached_prompt_tokens,
            input_cost_usd=round(input_cost, 8),
            output_cost_usd=round(output_cost, 8),
            total_cost_usd=round(total_cost, 8),
            input_price_per_1m=pricing.input_per_1m_tokens,
            output_price_per_1m=pricing.output_per_1m_tokens,
        )

    @staticmethod
    def estimate_cost(
        model_id: str,
        estimated_prompt_tokens: int,
        estimated_completion_tokens: int,
    ) -> float:
        """Quick cost estimate without full breakdown.  Returns total USD."""
        model = get_model_info(model_id)
        if not model:
            return 0.0
        pricing = model.pricing
        input_cost = (estimated_prompt_tokens / 1_000_000) * pricing.input_per_1m_tokens
        output_cost = (estimated_completion_tokens / 1_000_000) * pricing.output_per_1m_tokens
        return round(input_cost + output_cost, 8)

    @staticmethod
    def get_price_per_token(model_id: str, direction: str = "input") -> float:
        """Get the price per single token for a model."""
        model = get_model_info(model_id)
        if not model:
            return 0.0
        if direction == "output":
            return model.pricing.output_per_1m_tokens / 1_000_000
        return model.pricing.input_per_1m_tokens / 1_000_000


class CostBreakdown:
    """Detailed cost breakdown for a single request."""

    def __init__(
        self,
        model_id: str = "",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cached_prompt_tokens: int = 0,
        input_cost_usd: float = 0.0,
        output_cost_usd: float = 0.0,
        total_cost_usd: float = 0.0,
        input_price_per_1m: float = 0.0,
        output_price_per_1m: float = 0.0,
    ):
        self.model_id = model_id
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.cached_prompt_tokens = cached_prompt_tokens
        self.input_cost_usd = input_cost_usd
        self.output_cost_usd = output_cost_usd
        self.total_cost_usd = total_cost_usd
        self.input_price_per_1m = input_price_per_1m
        self.output_price_per_1m = output_price_per_1m

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_prompt_tokens": self.cached_prompt_tokens,
            "input_cost_usd": self.input_cost_usd,
            "output_cost_usd": self.output_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "input_price_per_1m": self.input_price_per_1m,
            "output_price_per_1m": self.output_price_per_1m,
        }
