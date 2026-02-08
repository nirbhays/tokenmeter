"""Tests for the Python SDK client."""

import pytest
from tokenmeter import OpenAI
from tokenmeter.client import TokenMeterClient


class TestPythonSDK:
    def test_import_as_openai(self):
        """Should be importable as OpenAI for drop-in replacement."""
        assert OpenAI is TokenMeterClient

    def test_default_config(self):
        client = TokenMeterClient(api_key="test-key", base_url="http://localhost:8000")
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8000"

    def test_has_chat_namespace(self):
        client = TokenMeterClient(api_key="test-key")
        assert hasattr(client, "chat")
        assert hasattr(client.chat, "completions")
        assert hasattr(client.chat.completions, "create")

    def test_has_models_namespace(self):
        client = TokenMeterClient(api_key="test-key")
        assert hasattr(client, "models")
        assert hasattr(client.models, "list")

    def test_context_manager(self):
        with TokenMeterClient(api_key="test-key") as client:
            assert client.api_key == "test-key"

    def test_version(self):
        import tokenmeter
        assert tokenmeter.__version__ == "0.1.0"
