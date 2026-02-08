"""Shared test fixtures."""

import asyncio
import pytest

from backend.config import Settings
from backend.models.proxy import (
    ChatCompletionRequest,
    ChatMessage,
    Role,
)
from backend.models.routing import RoutingConfig, RoutingMode


@pytest.fixture
def settings():
    return Settings(
        environment="development",
        openai_api_key="test-key",
        anthropic_api_key="test-key",
        google_api_key="test-key",
    )


@pytest.fixture
def simple_request():
    return ChatCompletionRequest(
        model="gpt-4.1",
        messages=[
            ChatMessage(role=Role.user, content="What is 2+2?"),
        ],
    )


@pytest.fixture
def complex_request():
    return ChatCompletionRequest(
        model="gpt-4.1",
        messages=[
            ChatMessage(
                role=Role.system,
                content=(
                    "You are an expert software architect. Analyze the following codebase "
                    "and provide a comprehensive architectural review with recommendations "
                    "for refactoring, performance optimization, and scalability improvements. "
                    "Consider design patterns, SOLID principles, and microservices patterns."
                ),
            ),
            ChatMessage(
                role=Role.user,
                content=(
                    "Here is our main application module with 500 lines of code that handles "
                    "user authentication, payment processing, and email notifications all in one file. "
                    "We need to refactor this into a clean architecture with proper separation of concerns. "
                    "The codebase uses async/await patterns and connects to PostgreSQL and Redis. "
                    "Please analyze the code structure, identify anti-patterns, and provide a step-by-step "
                    "refactoring plan with code examples for each step. Also consider how to implement "
                    "proper error handling, logging, and monitoring. ```python\nimport asyncio\n"
                    "import asyncpg\nimport redis\nfrom fastapi import FastAPI\n\nclass App:\n"
                    "    def __init__(self):\n        self.db = None\n        self.cache = None\n"
                    "    async def authenticate(self, token):\n        # complex auth logic\n"
                    "        pass\n    async def process_payment(self, amount):\n        # payment logic\n"
                    "        pass\n    async def send_email(self, to, subject, body):\n        # email logic\n"
                    "        pass\n```"
                ),
            ),
        ],
        max_tokens=8000,
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "search_codebase",
                    "description": "Search for patterns in the codebase",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                },
            }
        ],
    )


@pytest.fixture
def medium_request():
    return ChatCompletionRequest(
        model="gpt-4.1",
        messages=[
            ChatMessage(role=Role.system, content="You are a helpful assistant."),
            ChatMessage(role=Role.user, content="Explain the difference between REST and GraphQL APIs. Include pros, cons, and when to use each."),
        ],
        max_tokens=2000,
    )


@pytest.fixture
def routing_config():
    return RoutingConfig(
        org_id="test_org",
        mode=RoutingMode.cost_optimized,
        enabled=True,
    )
