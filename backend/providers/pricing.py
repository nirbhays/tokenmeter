"""
Comprehensive pricing table for all supported LLM providers and models.

Prices are in USD per 1 million tokens.  Last updated: February 2026.
"""

from __future__ import annotations

from backend.models.provider import (
    ModelCapability,
    ModelInfo,
    ModelPricing,
    ProviderName,
)

# ── Standard capability sets ──────────────────────────────────────────────────

_CHAT_FULL = [
    ModelCapability.chat,
    ModelCapability.streaming,
    ModelCapability.function_calling,
    ModelCapability.json_mode,
    ModelCapability.vision,
]

_CHAT_TEXT = [
    ModelCapability.chat,
    ModelCapability.streaming,
    ModelCapability.function_calling,
    ModelCapability.json_mode,
]

_EMBEDDING = [ModelCapability.embedding]

# ══════════════════════════════════════════════════════════════════════════════
#  OPENAI  (Feb 2026 pricing)
# ══════════════════════════════════════════════════════════════════════════════

OPENAI_MODELS: list[ModelInfo] = [
    # ── GPT-5 family ──────────────────────────────────────────────────
    ModelInfo(
        id="gpt-5.2",
        name="GPT-5.2",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=12.00, output_per_1m_tokens=40.00, cached_input_per_1m_tokens=3.00),
        context_window=256_000,
        max_output_tokens=32_768,
        capabilities=_CHAT_FULL,
        quality_score=0.99,
        speed_score=0.60,
        description="Most capable OpenAI model — ideal for complex reasoning, research, and agentic workflows.",
    ),
    ModelInfo(
        id="gpt-5",
        name="GPT-5",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=10.00, output_per_1m_tokens=30.00, cached_input_per_1m_tokens=2.50),
        context_window=256_000,
        max_output_tokens=32_768,
        capabilities=_CHAT_FULL,
        quality_score=0.97,
        speed_score=0.65,
        description="Flagship OpenAI model, excellent balance of quality and speed.",
    ),
    ModelInfo(
        id="gpt-5-mini",
        name="GPT-5 Mini",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=2.50, output_per_1m_tokens=10.00, cached_input_per_1m_tokens=0.625),
        context_window=256_000,
        max_output_tokens=16_384,
        capabilities=_CHAT_FULL,
        quality_score=0.90,
        speed_score=0.80,
        description="Smaller GPT-5 variant — fast and cost-effective for most tasks.",
    ),
    # ── GPT-4.1 family ────────────────────────────────────────────────
    ModelInfo(
        id="gpt-4.1",
        name="GPT-4.1",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=2.00, output_per_1m_tokens=8.00, cached_input_per_1m_tokens=0.50),
        context_window=1_047_576,
        max_output_tokens=32_768,
        capabilities=_CHAT_FULL,
        quality_score=0.88,
        speed_score=0.75,
        description="1M context window, strong coding and instruction following.",
    ),
    ModelInfo(
        id="gpt-4.1-mini",
        name="GPT-4.1 Mini",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=0.40, output_per_1m_tokens=1.60, cached_input_per_1m_tokens=0.10),
        context_window=1_047_576,
        max_output_tokens=32_768,
        capabilities=_CHAT_FULL,
        quality_score=0.82,
        speed_score=0.88,
        description="Fast and affordable with 1M context window.",
    ),
    ModelInfo(
        id="gpt-4.1-nano",
        name="GPT-4.1 Nano",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=0.10, output_per_1m_tokens=0.40, cached_input_per_1m_tokens=0.025),
        context_window=1_047_576,
        max_output_tokens=32_768,
        capabilities=_CHAT_TEXT,
        quality_score=0.72,
        speed_score=0.95,
        description="Fastest and cheapest — great for classification, extraction, simple completions.",
    ),
    # ── o-series (reasoning) ──────────────────────────────────────────
    ModelInfo(
        id="o3",
        name="o3",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=10.00, output_per_1m_tokens=40.00, cached_input_per_1m_tokens=2.50),
        context_window=200_000,
        max_output_tokens=100_000,
        capabilities=_CHAT_FULL,
        quality_score=0.97,
        speed_score=0.40,
        description="Deep reasoning model — excels at math, science, and complex logic.",
    ),
    ModelInfo(
        id="o4-mini",
        name="o4-mini",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=1.10, output_per_1m_tokens=4.40, cached_input_per_1m_tokens=0.275),
        context_window=200_000,
        max_output_tokens=100_000,
        capabilities=_CHAT_FULL,
        quality_score=0.92,
        speed_score=0.55,
        description="Cost-effective reasoning model.",
    ),
    # ── Embeddings ────────────────────────────────────────────────────
    ModelInfo(
        id="text-embedding-3-large",
        name="Text Embedding 3 Large",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=0.13, output_per_1m_tokens=0.0),
        context_window=8_191,
        capabilities=_EMBEDDING,
        quality_score=0.95,
        speed_score=0.90,
    ),
    ModelInfo(
        id="text-embedding-3-small",
        name="Text Embedding 3 Small",
        provider=ProviderName.openai,
        pricing=ModelPricing(input_per_1m_tokens=0.02, output_per_1m_tokens=0.0),
        context_window=8_191,
        capabilities=_EMBEDDING,
        quality_score=0.85,
        speed_score=0.95,
    ),
]

# ══════════════════════════════════════════════════════════════════════════════
#  ANTHROPIC  (Feb 2026 pricing)
# ══════════════════════════════════════════════════════════════════════════════

ANTHROPIC_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="claude-opus-4",
        name="Claude Opus 4",
        provider=ProviderName.anthropic,
        pricing=ModelPricing(input_per_1m_tokens=15.00, output_per_1m_tokens=75.00, cached_input_per_1m_tokens=1.875),
        context_window=200_000,
        max_output_tokens=32_000,
        capabilities=_CHAT_FULL,
        quality_score=0.98,
        speed_score=0.50,
        description="Anthropic's most capable model — excels at complex analysis and agentic coding.",
    ),
    ModelInfo(
        id="claude-sonnet-4.5",
        name="Claude Sonnet 4.5",
        provider=ProviderName.anthropic,
        pricing=ModelPricing(input_per_1m_tokens=3.00, output_per_1m_tokens=15.00, cached_input_per_1m_tokens=0.375),
        context_window=200_000,
        max_output_tokens=16_000,
        capabilities=_CHAT_FULL,
        quality_score=0.93,
        speed_score=0.75,
        description="Best balance of intelligence and speed in the Claude family.",
    ),
    ModelInfo(
        id="claude-haiku-3.5",
        name="Claude Haiku 3.5",
        provider=ProviderName.anthropic,
        pricing=ModelPricing(input_per_1m_tokens=0.80, output_per_1m_tokens=4.00, cached_input_per_1m_tokens=0.08),
        context_window=200_000,
        max_output_tokens=8_192,
        capabilities=_CHAT_TEXT,
        quality_score=0.82,
        speed_score=0.92,
        description="Fast and affordable — great for high-volume tasks.",
    ),
]

# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE  (Feb 2026 pricing)
# ══════════════════════════════════════════════════════════════════════════════

GOOGLE_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="gemini-2.5-pro",
        name="Gemini 2.5 Pro",
        provider=ProviderName.google,
        pricing=ModelPricing(input_per_1m_tokens=1.25, output_per_1m_tokens=10.00, cached_input_per_1m_tokens=0.3125),
        context_window=1_048_576,
        max_output_tokens=65_536,
        capabilities=_CHAT_FULL,
        quality_score=0.95,
        speed_score=0.65,
        description="Google's thinking model with 1M context — strong at reasoning and code.",
    ),
    ModelInfo(
        id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider=ProviderName.google,
        pricing=ModelPricing(input_per_1m_tokens=0.15, output_per_1m_tokens=0.60, cached_input_per_1m_tokens=0.0375),
        context_window=1_048_576,
        max_output_tokens=65_536,
        capabilities=_CHAT_FULL,
        quality_score=0.86,
        speed_score=0.92,
        description="Extremely fast and cheap with 1M context — Google's workhorse model.",
    ),
]

# ══════════════════════════════════════════════════════════════════════════════
#  COMBINED REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

ALL_MODELS: list[ModelInfo] = OPENAI_MODELS + ANTHROPIC_MODELS + GOOGLE_MODELS

# Fast lookup dicts
MODEL_BY_ID: dict[str, ModelInfo] = {m.id: m for m in ALL_MODELS}
MODELS_BY_PROVIDER: dict[ProviderName, list[ModelInfo]] = {}
for _m in ALL_MODELS:
    MODELS_BY_PROVIDER.setdefault(_m.provider, []).append(_m)


def get_model_info(model_id: str) -> ModelInfo | None:
    """Look up model info by ID.  Returns None if not found."""
    return MODEL_BY_ID.get(model_id)


def get_models_for_provider(provider: ProviderName) -> list[ModelInfo]:
    return MODELS_BY_PROVIDER.get(provider, [])


def get_all_model_ids() -> list[str]:
    return list(MODEL_BY_ID.keys())
