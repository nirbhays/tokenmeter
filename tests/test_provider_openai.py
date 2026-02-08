"""Tests for OpenAI provider adapter."""

import pytest
from backend.providers.openai import OpenAIProvider


class TestOpenAIProvider:
    def test_provider_name(self):
        provider = OpenAIProvider(api_key="test")
        assert provider.name == "openai"

    def test_api_base_url(self):
        provider = OpenAIProvider(api_key="test")
        assert provider.api_base_url == "https://api.openai.com/v1"

    def test_strip_tm_fields(self):
        provider = OpenAIProvider(api_key="test")
        body = {
            "model": "gpt-4.1",
            "messages": [{"role": "user", "content": "hi"}],
            "tm_team": "search",
            "x-tm-feature": "autocomplete",
            "x_tm_routing_mode": "cost",
            "temperature": 0.7,
        }
        cleaned = provider._strip_tm_fields(body)
        assert "model" in cleaned
        assert "messages" in cleaned
        assert "temperature" in cleaned
        assert "tm_team" not in cleaned
        assert "x-tm-feature" not in cleaned
        assert "x_tm_routing_mode" not in cleaned
