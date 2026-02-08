"""Stripe billing models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class Subscription(BaseModel):
    """Organization subscription details."""

    id: str
    org_id: str
    plan: PlanTier = PlanTier.free
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: str = "active"  # active | past_due | canceled | trialing
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

    # Plan limits
    monthly_request_limit: int = 10_000  # free tier
    monthly_token_limit: int = 1_000_000
    max_api_keys: int = 2
    max_team_members: int = 3
    features: List[str] = Field(default_factory=lambda: ["basic_dashboard", "cost_tracking"])


class PlanInfo(BaseModel):
    """Pricing plan details for display."""

    tier: PlanTier
    name: str
    price_monthly_usd: float
    price_yearly_usd: float
    monthly_request_limit: int
    monthly_token_limit: int
    max_api_keys: int
    max_team_members: int
    features: List[str]
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None


PLANS: List[PlanInfo] = [
    PlanInfo(
        tier=PlanTier.free,
        name="Free",
        price_monthly_usd=0.0,
        price_yearly_usd=0.0,
        monthly_request_limit=10_000,
        monthly_token_limit=1_000_000,
        max_api_keys=2,
        max_team_members=3,
        features=[
            "basic_dashboard",
            "cost_tracking",
            "2_api_keys",
            "7_day_retention",
        ],
    ),
    PlanInfo(
        tier=PlanTier.pro,
        name="Pro",
        price_monthly_usd=49.0,
        price_yearly_usd=470.0,
        monthly_request_limit=500_000,
        monthly_token_limit=50_000_000,
        max_api_keys=20,
        max_team_members=20,
        features=[
            "advanced_dashboard",
            "cost_tracking",
            "smart_routing",
            "budget_alerts",
            "20_api_keys",
            "90_day_retention",
            "team_management",
            "slack_integration",
            "webhook_alerts",
            "response_caching",
        ],
    ),
    PlanInfo(
        tier=PlanTier.enterprise,
        name="Enterprise",
        price_monthly_usd=299.0,
        price_yearly_usd=2870.0,
        monthly_request_limit=10_000_000,
        monthly_token_limit=1_000_000_000,
        max_api_keys=100,
        max_team_members=999,
        features=[
            "advanced_dashboard",
            "cost_tracking",
            "smart_routing",
            "budget_alerts",
            "unlimited_api_keys",
            "unlimited_retention",
            "team_management",
            "slack_integration",
            "webhook_alerts",
            "response_caching",
            "semantic_caching",
            "custom_routing_rules",
            "sso",
            "sla",
            "dedicated_support",
            "zero_logging_mode",
            "data_residency",
        ],
    ),
]


class CheckoutSessionRequest(BaseModel):
    plan: PlanTier
    billing_period: str = "monthly"  # monthly | yearly


class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class InvoiceSummary(BaseModel):
    id: str
    amount_usd: float
    status: str
    period_start: datetime
    period_end: datetime
    pdf_url: Optional[str] = None
