"""
Request Classifier — determines the complexity of an incoming LLM request.

The complexity score drives the Smart Router: simple requests go to cheap
models (e.g. GPT-4.1-nano), complex ones go to powerful models (e.g. GPT-5.2).

Heuristic classification uses multiple signals:
  - Message length / token count
  - System prompt complexity
  - Presence of tool/function calls
  - Conversation depth (number of turns)
  - Keyword signals (code, math, analysis, etc.)
"""

from __future__ import annotations

import re
import logging
from typing import List

from backend.models.proxy import ChatCompletionRequest, ChatMessage, Role
from backend.models.routing import ComplexityLevel

logger = logging.getLogger(__name__)

# ── Complexity keyword sets ───────────────────────────────────────────────────

COMPLEX_KEYWORDS = {
    # Reasoning & analysis
    "analyze", "analysis", "evaluate", "compare", "contrast", "synthesize",
    "critique", "assess", "investigate", "examine", "deduce", "infer",
    # Code / technical
    "implement", "refactor", "debug", "architecture", "algorithm", "optimize",
    "design pattern", "data structure", "complexity", "recursive",
    "async", "concurrent", "distributed", "microservice",
    # Math / science
    "prove", "theorem", "equation", "integral", "derivative", "probability",
    "statistical", "regression", "hypothesis", "correlation",
    # Creative / long-form
    "write an essay", "write a story", "write a report", "detailed explanation",
    "comprehensive", "in-depth", "step by step", "step-by-step",
    # Multi-step reasoning
    "first.*then.*finally", "chain of thought", "reasoning",
    "break down", "walk me through",
}

SIMPLE_KEYWORDS = {
    "translate", "summarize", "summary", "tldr", "classify", "categorize",
    "extract", "yes or no", "true or false", "one word", "short answer",
    "list", "name", "define", "what is", "who is", "when did",
    "convert", "format", "rewrite", "rephrase",
}


class RequestClassifier:
    """Classifies request complexity using heuristic signals."""

    @staticmethod
    def classify(request: ChatCompletionRequest) -> tuple[ComplexityLevel, float]:
        """
        Classify a request's complexity.

        Returns:
            (ComplexityLevel, score) where score is 0.0-1.0
        """
        score = 0.0
        signals: list[str] = []

        messages = request.messages

        # ── Signal 1: Total message length ────────────────────────────
        total_chars = sum(
            len(m.content) if isinstance(m.content, str) else 0
            for m in messages
            if m.content
        )

        if total_chars > 5000:
            score += 0.25
            signals.append(f"long_input({total_chars})")
        elif total_chars > 1500:
            score += 0.15
            signals.append(f"medium_input({total_chars})")
        elif total_chars < 200:
            score -= 0.1
            signals.append(f"short_input({total_chars})")

        # ── Signal 2: Conversation depth ──────────────────────────────
        user_messages = [m for m in messages if m.role == Role.user]
        num_turns = len(user_messages)

        if num_turns > 5:
            score += 0.15
            signals.append(f"deep_conversation({num_turns}_turns)")
        elif num_turns > 2:
            score += 0.05
        elif num_turns == 1:
            score -= 0.05

        # ── Signal 3: System prompt complexity ────────────────────────
        system_msgs = [m for m in messages if m.role == Role.system]
        if system_msgs:
            sys_text = " ".join(
                m.content if isinstance(m.content, str) else ""
                for m in system_msgs
            )
            sys_len = len(sys_text)
            if sys_len > 2000:
                score += 0.15
                signals.append(f"complex_system_prompt({sys_len})")
            elif sys_len > 500:
                score += 0.05

        # ── Signal 4: Tool / function calling ─────────────────────────
        if request.tools and len(request.tools) > 0:
            score += 0.2
            signals.append(f"tools({len(request.tools)})")
        if any(m.tool_calls for m in messages if m.tool_calls):
            score += 0.1
            signals.append("has_tool_calls")

        # ── Signal 5: Keyword analysis ────────────────────────────────
        all_text = " ".join(
            m.content.lower() if isinstance(m.content, str) else ""
            for m in messages
            if m.content
        )

        complex_hits = sum(1 for kw in COMPLEX_KEYWORDS if kw in all_text)
        simple_hits = sum(1 for kw in SIMPLE_KEYWORDS if kw in all_text)

        if complex_hits > 3:
            score += 0.25
            signals.append(f"complex_keywords({complex_hits})")
        elif complex_hits > 1:
            score += 0.1

        if simple_hits > 2:
            score -= 0.15
            signals.append(f"simple_keywords({simple_hits})")
        elif simple_hits > 0:
            score -= 0.05

        # ── Signal 6: Requested output length ─────────────────────────
        max_tok = request.max_tokens or request.max_completion_tokens
        if max_tok:
            if max_tok > 4000:
                score += 0.15
                signals.append(f"long_output({max_tok})")
            elif max_tok < 100:
                score -= 0.1
                signals.append(f"short_output({max_tok})")

        # ── Signal 7: JSON mode / structured output ───────────────────
        if request.response_format and request.response_format.type != "text":
            score += 0.05
            signals.append("structured_output")

        # ── Signal 8: Code patterns in content ────────────────────────
        code_patterns = [r"```", r"def\s+\w+", r"class\s+\w+", r"import\s+", r"function\s+\w+"]
        code_hits = sum(1 for p in code_patterns if re.search(p, all_text))
        if code_hits >= 3:
            score += 0.15
            signals.append(f"code_content({code_hits})")
        elif code_hits >= 1:
            score += 0.05

        # ── Clamp and classify ────────────────────────────────────────
        score = max(0.0, min(1.0, score))

        if score >= 0.55:
            level = ComplexityLevel.complex
        elif score >= 0.25:
            level = ComplexityLevel.medium
        else:
            level = ComplexityLevel.simple

        logger.debug(
            "Classified request: %s (score=%.2f, signals=%s)",
            level.value,
            score,
            signals,
        )

        return level, round(score, 3)
