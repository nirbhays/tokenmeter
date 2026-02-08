"""
API Key management endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.utils.security import generate_api_key, hash_api_key, mask_api_key
from backend.middleware.auth import register_api_key

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


class ApiKeyInfo(BaseModel):
    id: str
    name: str
    masked_key: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    scopes: List[str] = ["proxy", "dashboard"]


class ApiKeyCreate(BaseModel):
    name: str = "default"
    scopes: List[str] = Field(default_factory=lambda: ["proxy", "dashboard"])


class ApiKeyCreateResponse(BaseModel):
    key: str  # Full key — shown ONCE
    id: str
    name: str
    masked_key: str
    created_at: datetime
    warning: str = "Store this key securely. It will not be shown again."


# In-memory key store for dev
_keys: dict[str, ApiKeyInfo] = {}


@router.get("/", response_model=List[ApiKeyInfo])
async def list_keys(request: Request):
    """List all API keys (masked) for the current organization."""
    org_id = getattr(request.state, "org_id", "default")
    return [k for k in _keys.values()]


@router.post("/", response_model=ApiKeyCreateResponse)
async def create_key(body: ApiKeyCreate, request: Request):
    """Create a new API key."""
    org_id = getattr(request.state, "org_id", "default")

    raw_key = generate_api_key()
    key_id = hash_api_key(raw_key)[:12]

    # Register in auth middleware
    register_api_key(raw_key, org_id, key_id, body.name, body.scopes)

    # Store metadata
    info = ApiKeyInfo(
        id=key_id,
        name=body.name,
        masked_key=mask_api_key(raw_key),
        created_at=datetime.utcnow(),
        scopes=body.scopes,
    )
    _keys[key_id] = info

    return ApiKeyCreateResponse(
        key=raw_key,
        id=key_id,
        name=body.name,
        masked_key=info.masked_key,
        created_at=info.created_at,
    )


@router.delete("/{key_id}")
async def delete_key(key_id: str, request: Request):
    """Revoke an API key."""
    if key_id in _keys:
        del _keys[key_id]
    return {"status": "revoked", "key_id": key_id}
