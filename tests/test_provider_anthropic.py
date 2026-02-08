"""Tests for Anthropic provider adapter."""

import pytest
from backend.providers.anthropic import AnthropicProvider, ANTHROPIC_MODEL_MAP
from backend.models.proxy import ChatMessage, Role


class TestAnthropicProvider:
    def test_provider_name(self):
        provider = AnthropicProvider(api_key="test")
        assert provider.name == "anthropic"

    def test_model_mapping(self):
        assert "claude-opus-4" in ANTHROPIC_MODEL_MAP
        assert "claude-sonnet-4.5" in ANTHROPIC_MODEL_MAP
        assert "claude-haiku-3.5" in ANTHROPIC_MODEL_MAP

    def test_convert_messages_extracts_system(self):
        provider = AnthropicProvider(api_key="test")
        messages = [
            ChatMessage(role=Role.system, content="You are helpful."),
            ChatMessage(role=Role.user, content="Hello!"),
        ]
        system, converted = provider._convert_messages(messages)
        assert system == "You are helpful."
        assert len(converted) == 1
        assert converted[0]["role"] == "user"
        assert converted[0]["content"] == "Hello!"

    def test_convert_messages_no_system(self):
        provider = AnthropicProvider(api_key="test")
        messages = [
            ChatMessage(role=Role.user, content="Hello!"),
            ChatMessage(role=Role.assistant, content="Hi there!"),
        ]
        system, converted = provider._convert_messages(messages)
        assert system is None
        assert len(converted) == 2
        assert converted[0]["role"] == "user"
        assert converted[1]["role"] == "assistant"
