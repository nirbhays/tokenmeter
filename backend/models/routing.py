"""Routing configuration models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoutingMode(str, Enum):
    cost_optimized = "cost-optimized"
    latency_optimized = "latency-optimized"
    quality_optimized = "quality-optimized"
    custom = "custom"


class ComplexityLevel(str, Enum):
    simple = "simple"
    medium = "medium"
    complex = "complex"


class RoutingRule(BaseModel):
    """A single routing rule that maps conditions to a target model."""

    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    priority: int = 0  # higher = evaluated first
    enabled: bool = True

    # Conditions
    source_models: List[str] = Field(default_factory=list, description="Models this rule applies to, e.g. ['gpt-4.1']")
    complexity_levels: List[ComplexityLevel] = Field(default_factory=list)
    teams: List[str] = Field(default_factory=list, description="Team tags this rule applies to")
    features: List[str] = Field(default_factory=list, description="Feature tags this rule applies to")
    max_tokens_threshold: Optional[int] = None
    min_tokens_threshold: Optional[int] = None

    # Target
    target_model: str
    target_provider: Optional[str] = None

    # Fallback
    fallback_model: Optional[str] = None


class RoutingConfig(BaseModel):
    """Complete routing configuration for an organization."""

    org_id: str
    mode: RoutingMode = RoutingMode.cost_optimized
    enabled: bool = True
    rules: List[RoutingRule] = Field(default_factory=list)

    # Model mappings (simple override: requested → actual)
    model_aliases: Dict[str, str] = Field(default_factory=dict)

    # Fallback chain
    fallback_models: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Fallback chain per model, e.g. {'gpt-5.2': ['gpt-5', 'gpt-4.1']}",
    )


class RoutingDecision(BaseModel):
    """The result of the routing engine's evaluation."""

    original_model: str
    routed_model: str
    provider: str
    reason: str  # human-readable explanation
    rule_id: Optional[str] = None
    complexity: Optional[ComplexityLevel] = None
    complexity_score: Optional[float] = None
    was_rerouted: bool = False


class RoutingRuleCreate(BaseModel):
    """Schema for creating a routing rule."""

    name: str
    description: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    source_models: List[str] = Field(default_factory=list)
    complexity_levels: List[ComplexityLevel] = Field(default_factory=list)
    teams: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    max_tokens_threshold: Optional[int] = None
    min_tokens_threshold: Optional[int] = None
    target_model: str
    target_provider: Optional[str] = None
    fallback_model: Optional[str] = None


class RoutingConfigUpdate(BaseModel):
    """Schema for updating routing config."""

    mode: Optional[RoutingMode] = None
    enabled: Optional[bool] = None
    model_aliases: Optional[Dict[str, str]] = None
    fallback_models: Optional[Dict[str, List[str]]] = None
