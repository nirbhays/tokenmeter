"""
Routing configuration endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from backend.models.routing import (
    RoutingConfig,
    RoutingConfigUpdate,
    RoutingRule,
    RoutingRuleCreate,
)
from backend.providers.pricing import ALL_MODELS

router = APIRouter(prefix="/api/routing", tags=["Routing"])

# In-memory routing configs (replace with DB in production)
_configs: dict[str, RoutingConfig] = {}


def _get_or_create_config(org_id: str) -> RoutingConfig:
    if org_id not in _configs:
        _configs[org_id] = RoutingConfig(org_id=org_id)
    return _configs[org_id]


@router.get("/config")
async def get_routing_config(request: Request):
    """Get routing configuration for the current organization."""
    org_id = getattr(request.state, "org_id", "default")
    config = _get_or_create_config(org_id)
    return config.model_dump()


@router.put("/config")
async def update_routing_config(body: RoutingConfigUpdate, request: Request):
    """Update routing configuration."""
    org_id = getattr(request.state, "org_id", "default")
    config = _get_or_create_config(org_id)

    if body.mode is not None:
        config.mode = body.mode
    if body.enabled is not None:
        config.enabled = body.enabled
    if body.model_aliases is not None:
        config.model_aliases = body.model_aliases
    if body.fallback_models is not None:
        config.fallback_models = body.fallback_models

    return config.model_dump()


@router.get("/rules")
async def list_routing_rules(request: Request):
    """List all routing rules."""
    org_id = getattr(request.state, "org_id", "default")
    config = _get_or_create_config(org_id)
    return {"data": [r.model_dump() for r in config.rules]}


@router.post("/rules")
async def create_routing_rule(body: RoutingRuleCreate, request: Request):
    """Create a new routing rule."""
    org_id = getattr(request.state, "org_id", "default")
    config = _get_or_create_config(org_id)

    import uuid
    rule = RoutingRule(
        id=uuid.uuid4().hex[:12],
        **body.model_dump(),
    )
    config.rules.append(rule)
    return rule.model_dump()


@router.delete("/rules/{rule_id}")
async def delete_routing_rule(rule_id: str, request: Request):
    """Delete a routing rule."""
    org_id = getattr(request.state, "org_id", "default")
    config = _get_or_create_config(org_id)
    config.rules = [r for r in config.rules if r.id != rule_id]
    return {"status": "deleted", "rule_id": rule_id}


@router.get("/models")
async def list_available_models(request: Request):
    """List all models with pricing and capability info."""
    return {
        "data": [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider.value,
                "pricing": m.pricing.model_dump(),
                "context_window": m.context_window,
                "quality_score": m.quality_score,
                "speed_score": m.speed_score,
                "capabilities": [c.value for c in m.capabilities],
            }
            for m in ALL_MODELS
        ]
    }
