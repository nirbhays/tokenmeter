"""
Billing Service — Stripe integration for subscription management.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.config import get_settings
from backend.models.billing import (
    BillingPortalResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    InvoiceSummary,
    PLANS,
    PlanInfo,
    PlanTier,
    Subscription,
)

logger = logging.getLogger(__name__)


class BillingService:
    """Handles Stripe subscription management."""

    def __init__(self):
        self._stripe = None

    async def initialize(self) -> None:
        settings = get_settings()
        if not settings.stripe_secret_key:
            logger.warning("Stripe secret key not configured — billing disabled")
            return

        try:
            import stripe

            stripe.api_key = settings.stripe_secret_key
            self._stripe = stripe
            logger.info("Stripe billing service initialized")
        except ImportError:
            logger.warning("stripe package not installed — billing disabled")

    def get_plans(self) -> list[PlanInfo]:
        return PLANS

    def get_plan(self, tier: PlanTier) -> Optional[PlanInfo]:
        for plan in PLANS:
            if plan.tier == tier:
                return plan
        return None

    async def create_checkout_session(
        self,
        org_id: str,
        request: CheckoutSessionRequest,
    ) -> CheckoutSessionResponse:
        """Create a Stripe Checkout session for upgrading."""
        if not self._stripe:
            raise RuntimeError("Stripe not configured")

        settings = get_settings()
        plan = self.get_plan(request.plan)
        if not plan:
            raise ValueError(f"Unknown plan: {request.plan}")

        price_id = (
            plan.stripe_price_id_yearly
            if request.billing_period == "yearly"
            else plan.stripe_price_id_monthly
        )

        if not price_id:
            # Use settings-based fallback
            price_map = {
                PlanTier.pro: settings.stripe_price_id_pro,
                PlanTier.enterprise: settings.stripe_price_id_enterprise,
            }
            price_id = price_map.get(request.plan)

        if not price_id:
            raise ValueError(f"No Stripe price ID configured for {request.plan}")

        session = self._stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.frontend_url}/dashboard/settings?checkout=success",
            cancel_url=f"{settings.frontend_url}/dashboard/settings?checkout=canceled",
            metadata={"org_id": org_id},
        )

        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
        )

    async def create_billing_portal(self, stripe_customer_id: str) -> BillingPortalResponse:
        """Create a Stripe Customer Portal session."""
        if not self._stripe:
            raise RuntimeError("Stripe not configured")

        settings = get_settings()
        session = self._stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{settings.frontend_url}/dashboard/settings",
        )
        return BillingPortalResponse(portal_url=session.url)

    async def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """Process a Stripe webhook event."""
        if not self._stripe:
            raise RuntimeError("Stripe not configured")

        settings = get_settings()
        try:
            event = self._stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
        except Exception as e:
            logger.error("Stripe webhook verification failed: %s", e)
            raise

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            org_id = data.get("metadata", {}).get("org_id")
            logger.info("Checkout completed for org %s", org_id)
            # TODO: Update org subscription in database
            return {"action": "subscription_created", "org_id": org_id}

        elif event_type == "customer.subscription.updated":
            logger.info("Subscription updated: %s", data.get("id"))
            return {"action": "subscription_updated"}

        elif event_type == "customer.subscription.deleted":
            logger.info("Subscription canceled: %s", data.get("id"))
            return {"action": "subscription_canceled"}

        elif event_type == "invoice.payment_failed":
            logger.warning("Payment failed for customer %s", data.get("customer"))
            return {"action": "payment_failed"}

        return {"action": "ignored", "event_type": event_type}


# Singleton
_billing: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    global _billing
    if _billing is None:
        _billing = BillingService()
    return _billing
