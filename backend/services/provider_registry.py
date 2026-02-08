"""
Provider Registry — manages all LLM provider instances and provides lookup.

Central place to get a provider adapter by name or model ID.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from backend.config import get_settings
from backend.models.provider import ModelInfo, ProviderHealth, ProviderName
from backend.providers.base import BaseLLMProvider
from backend.providers.openai import OpenAIProvider
from backend.providers.anthropic import AnthropicProvider
from backend.providers.google import GoogleProvider
from backend.providers.pricing import (
    ALL_MODELS,
    MODEL_BY_ID,
    MODELS_BY_PROVIDER,
    get_model_info,
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Singleton registry that holds provider adapter instances and model metadata.

    Usage:
        registry = ProviderRegistry()
        await registry.initialize()
        provider = registry.get_provider_for_model("gpt-4.1")
    """

    def __init__(self):
        self._providers: Dict[ProviderName, BaseLLMProvider] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Create provider instances from configured API keys."""
        if self._initialized:
            return

        settings = get_settings()

        if settings.openai_api_key:
            self._providers[ProviderName.openai] = OpenAIProvider(
                api_key=settings.openai_api_key,
                timeout=settings.proxy_timeout_seconds,
                max_retries=settings.proxy_max_retries,
            )
            logger.info("OpenAI provider initialized (%d models)", len(MODELS_BY_PROVIDER.get(ProviderName.openai, [])))

        if settings.anthropic_api_key:
            self._providers[ProviderName.anthropic] = AnthropicProvider(
                api_key=settings.anthropic_api_key,
                timeout=settings.proxy_timeout_seconds,
                max_retries=settings.proxy_max_retries,
            )
            logger.info("Anthropic provider initialized (%d models)", len(MODELS_BY_PROVIDER.get(ProviderName.anthropic, [])))

        if settings.google_api_key:
            self._providers[ProviderName.google] = GoogleProvider(
                api_key=settings.google_api_key,
                timeout=settings.proxy_timeout_seconds,
                max_retries=settings.proxy_max_retries,
            )
            logger.info("Google provider initialized (%d models)", len(MODELS_BY_PROVIDER.get(ProviderName.google, [])))

        self._initialized = True
        logger.info(
            "Provider registry ready: %d providers, %d models",
            len(self._providers),
            len(ALL_MODELS),
        )

    def get_provider(self, provider_name: ProviderName) -> Optional[BaseLLMProvider]:
        """Get a provider adapter by name."""
        return self._providers.get(provider_name)

    def get_provider_for_model(self, model_id: str) -> Optional[BaseLLMProvider]:
        """Look up which provider handles a model and return its adapter."""
        model_info = MODEL_BY_ID.get(model_id)
        if not model_info:
            return None
        return self._providers.get(model_info.provider)

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get model metadata."""
        return MODEL_BY_ID.get(model_id)

    def is_model_available(self, model_id: str) -> bool:
        """Check if a model is available (known + provider configured)."""
        model = MODEL_BY_ID.get(model_id)
        if not model:
            return False
        return model.provider in self._providers

    def list_available_models(self) -> list[ModelInfo]:
        """List all models whose providers are configured."""
        return [m for m in ALL_MODELS if m.provider in self._providers]

    def list_providers(self) -> list[ProviderName]:
        """List configured provider names."""
        return list(self._providers.keys())

    async def health_check_all(self) -> list[ProviderHealth]:
        """Run health checks on all configured providers."""
        results = []
        for name, provider in self._providers.items():
            try:
                healthy = await provider.health_check()
                models = MODELS_BY_PROVIDER.get(name, [])
                results.append(
                    ProviderHealth(
                        provider=name,
                        status="healthy" if healthy else "down",
                        active_models=len(models),
                    )
                )
            except Exception as e:
                logger.warning("Health check failed for %s: %s", name, e)
                results.append(ProviderHealth(provider=name, status="down"))
        return results

    async def shutdown(self) -> None:
        """Gracefully close all provider clients."""
        for name, provider in self._providers.items():
            try:
                if hasattr(provider, "close"):
                    await provider.close()
            except Exception as e:
                logger.warning("Error closing provider %s: %s", name, e)
        self._providers.clear()
        self._initialized = False


# Module-level singleton
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
