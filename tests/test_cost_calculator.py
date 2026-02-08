"""Tests for cost calculation."""

import pytest

from backend.services.cost_calculator import CostCalculator


class TestCostCalculator:
    def test_gpt41_nano_cost(self):
        """GPT-4.1-nano: $0.10/1M input, $0.40/1M output."""
        result = CostCalculator.calculate("gpt-4.1-nano", prompt_tokens=1000, completion_tokens=500)
        expected_input = (1000 / 1_000_000) * 0.10   # $0.0001
        expected_output = (500 / 1_000_000) * 0.40    # $0.0002
        assert abs(result.total_cost_usd - (expected_input + expected_output)) < 1e-8

    def test_gpt5_cost(self):
        """GPT-5: $10/1M input, $30/1M output."""
        result = CostCalculator.calculate("gpt-5", prompt_tokens=10000, completion_tokens=5000)
        expected_input = (10000 / 1_000_000) * 10.0   # $0.10
        expected_output = (5000 / 1_000_000) * 30.0    # $0.15
        assert abs(result.total_cost_usd - 0.25) < 1e-6

    def test_claude_opus_cost(self):
        """Claude Opus 4: $15/1M input, $75/1M output."""
        result = CostCalculator.calculate("claude-opus-4", prompt_tokens=5000, completion_tokens=2000)
        expected_input = (5000 / 1_000_000) * 15.0    # $0.075
        expected_output = (2000 / 1_000_000) * 75.0    # $0.15
        assert abs(result.total_cost_usd - (expected_input + expected_output)) < 1e-6

    def test_gemini_flash_cost(self):
        """Gemini 2.5 Flash: $0.15/1M input, $0.60/1M output."""
        result = CostCalculator.calculate("gemini-2.5-flash", prompt_tokens=50000, completion_tokens=10000)
        expected_input = (50000 / 1_000_000) * 0.15
        expected_output = (10000 / 1_000_000) * 0.60
        assert abs(result.total_cost_usd - (expected_input + expected_output)) < 1e-6

    def test_unknown_model_returns_zero(self):
        result = CostCalculator.calculate("nonexistent-model", prompt_tokens=1000, completion_tokens=500)
        assert result.total_cost_usd == 0.0

    def test_zero_tokens(self):
        result = CostCalculator.calculate("gpt-4.1", prompt_tokens=0, completion_tokens=0)
        assert result.total_cost_usd == 0.0

    def test_cached_input_discount(self):
        """Cached input tokens should use the cheaper rate."""
        result = CostCalculator.calculate(
            "gpt-4.1",
            prompt_tokens=10000,
            completion_tokens=1000,
            cached_prompt_tokens=8000,
        )
        # 2000 tokens at $2.00/1M + 8000 tokens at $0.50/1M
        non_cached_cost = (2000 / 1_000_000) * 2.00
        cached_cost = (8000 / 1_000_000) * 0.50
        output_cost = (1000 / 1_000_000) * 8.00
        expected = non_cached_cost + cached_cost + output_cost
        assert abs(result.total_cost_usd - expected) < 1e-6

    def test_estimate_cost(self):
        cost = CostCalculator.estimate_cost("gpt-4.1-mini", 10000, 5000)
        assert cost > 0
        # $0.40/1M input + $1.60/1M output
        expected = (10000 / 1_000_000) * 0.40 + (5000 / 1_000_000) * 1.60
        assert abs(cost - expected) < 1e-6

    def test_embedding_cost(self):
        """Embedding models: output cost is 0."""
        result = CostCalculator.calculate("text-embedding-3-small", prompt_tokens=1000, completion_tokens=0)
        expected = (1000 / 1_000_000) * 0.02
        assert abs(result.total_cost_usd - expected) < 1e-8
        assert result.output_cost_usd == 0.0

    def test_cost_breakdown_fields(self):
        result = CostCalculator.calculate("gpt-4.1", prompt_tokens=5000, completion_tokens=2000)
        assert result.model_id == "gpt-4.1"
        assert result.prompt_tokens == 5000
        assert result.completion_tokens == 2000
        assert result.input_cost_usd > 0
        assert result.output_cost_usd > 0
        assert result.total_cost_usd == result.input_cost_usd + result.output_cost_usd
