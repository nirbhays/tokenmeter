"""Tests for the request classifier."""

import pytest

from backend.models.proxy import ChatCompletionRequest, ChatMessage, Role
from backend.models.routing import ComplexityLevel
from backend.services.request_classifier import RequestClassifier


class TestRequestClassifier:
    def test_simple_question(self, simple_request):
        level, score = RequestClassifier.classify(simple_request)
        assert level == ComplexityLevel.simple
        assert score < 0.25

    def test_complex_request(self, complex_request):
        level, score = RequestClassifier.classify(complex_request)
        assert level == ComplexityLevel.complex
        assert score >= 0.55

    def test_medium_request(self, medium_request):
        level, score = RequestClassifier.classify(medium_request)
        assert level == ComplexityLevel.medium
        assert 0.25 <= score < 0.55

    def test_short_translation(self):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Translate 'hello' to French")],
        )
        level, score = RequestClassifier.classify(request)
        assert level == ComplexityLevel.simple

    def test_code_generation_is_complex(self):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[
                ChatMessage(role=Role.system, content="You are an expert Python developer."),
                ChatMessage(
                    role=Role.user,
                    content=(
                        "Implement a distributed task queue with the following requirements:\n"
                        "- Async workers with concurrent execution\n"
                        "- Redis-backed message broker\n"
                        "- Dead letter queue for failed tasks\n"
                        "- Retry logic with exponential backoff\n"
                        "- Priority queues\n"
                        "```python\nimport asyncio\nimport redis\n\nclass TaskQueue:\n    pass\n```"
                    ),
                ),
            ],
            max_tokens=4000,
        )
        level, score = RequestClassifier.classify(request)
        assert level in (ComplexityLevel.medium, ComplexityLevel.complex)

    def test_tool_calls_increase_complexity(self):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Search for the latest news")],
            tools=[
                {"type": "function", "function": {"name": "search", "parameters": {}}},
                {"type": "function", "function": {"name": "fetch", "parameters": {}}},
                {"type": "function", "function": {"name": "analyze", "parameters": {}}},
            ],
        )
        level, score = RequestClassifier.classify(request)
        # Tools add complexity
        assert score > 0.1

    def test_yes_no_question(self):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="Is Python a programming language? Yes or no.")],
            max_tokens=10,
        )
        level, score = RequestClassifier.classify(request)
        assert level == ComplexityLevel.simple

    def test_multi_turn_conversation(self):
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[
                ChatMessage(role=Role.user, content="What is machine learning?"),
                ChatMessage(role=Role.assistant, content="Machine learning is a subset of AI..."),
                ChatMessage(role=Role.user, content="How does it differ from deep learning?"),
                ChatMessage(role=Role.assistant, content="Deep learning is a subset of ML..."),
                ChatMessage(role=Role.user, content="Can you compare supervised vs unsupervised?"),
                ChatMessage(role=Role.assistant, content="Supervised learning uses labeled data..."),
                ChatMessage(role=Role.user, content="Now explain reinforcement learning with examples."),
            ],
        )
        level, score = RequestClassifier.classify(request)
        # Deep conversation = more complex
        assert score > 0.1

    def test_score_always_between_0_and_1(self):
        # Very long input
        request = ChatCompletionRequest(
            model="gpt-4.1",
            messages=[ChatMessage(role=Role.user, content="x " * 10000)],
        )
        level, score = RequestClassifier.classify(request)
        assert 0.0 <= score <= 1.0
