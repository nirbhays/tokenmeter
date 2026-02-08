"""
Billing endpoints — Stripe checkout, portal, webhooks.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.models.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    BillingPortalResponse,
    PLANS,
)
from backend.services.billing_service import get_billing_service

router = APIRouter(prefix="/api/billing", tags=["Billing"])


@router.get("/plans")
async def list_plans():
    """List all available pricing plans."""
    return {"data": [p.model_dump() for p in PLANS]}


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout(body: CheckoutSessionRequest, request: Request):
    """Create a Stripe Checkout session for upgrading."""
    org_id = getattr(request.state, "org_id", "default")
    billing = get_billing_service()

    try:
        return await billing.create_checkout_session(org_id, body)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal", response_model=BillingPortalResponse)
async def billing_portal(request: Request):
    """Create a Stripe Customer Portal session."""
    billing = get_billing_service()
    # In production, get stripe_customer_id from database
    stripe_customer_id = "cus_placeholder"

    try:
        return await billing.create_billing_portal(stripe_customer_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    billing = get_billing_service()
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    try:
        result = await billing.handle_webhook(payload, signature)
        return result
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
