"""Budget alert models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class BudgetPeriod(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class AlertChannel(str, Enum):
    slack = "slack"
    webhook = "webhook"
    email = "email"


class AlertSeverity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class BudgetThreshold(BaseModel):
    """A percentage threshold that triggers an alert."""

    percentage: float = Field(ge=0.0, le=200.0, description="Percentage of budget (e.g. 80 means 80%)")
    severity: AlertSeverity = AlertSeverity.warning
    channels: List[AlertChannel] = Field(default_factory=lambda: [AlertChannel.slack])
    notified: bool = False
    notified_at: Optional[datetime] = None


class Budget(BaseModel):
    """Budget definition for an organization or team."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    org_id: str
    name: str
    team: Optional[str] = None  # None = org-wide budget
    feature: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None

    amount_usd: float = Field(ge=0.0, description="Budget amount in USD")
    period: BudgetPeriod = BudgetPeriod.monthly

    thresholds: List[BudgetThreshold] = Field(
        default_factory=lambda: [
            BudgetThreshold(percentage=50.0, severity=AlertSeverity.info),
            BudgetThreshold(percentage=80.0, severity=AlertSeverity.warning),
            BudgetThreshold(percentage=100.0, severity=AlertSeverity.critical),
        ]
    )

    # Current spend tracking
    current_spend_usd: float = 0.0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Hard limit (block requests when exceeded)
    hard_limit: bool = False

    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetAlert(BaseModel):
    """Record of a triggered budget alert."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    budget_id: str
    org_id: str
    threshold_percentage: float
    severity: AlertSeverity
    current_spend_usd: float
    budget_amount_usd: float
    utilization_percentage: float
    message: str
    channels_notified: List[AlertChannel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BudgetCreate(BaseModel):
    """Schema for creating a budget."""

    name: str
    team: Optional[str] = None
    feature: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    amount_usd: float = Field(ge=0.0)
    period: BudgetPeriod = BudgetPeriod.monthly
    thresholds: Optional[List[BudgetThreshold]] = None
    hard_limit: bool = False


class BudgetUpdate(BaseModel):
    """Schema for updating a budget."""

    name: Optional[str] = None
    amount_usd: Optional[float] = Field(default=None, ge=0.0)
    period: Optional[BudgetPeriod] = None
    thresholds: Optional[List[BudgetThreshold]] = None
    hard_limit: Optional[bool] = None
    enabled: Optional[bool] = None


class BudgetStatus(BaseModel):
    """Current status of a budget."""

    budget: Budget
    utilization_percentage: float
    remaining_usd: float
    projected_end_of_period_usd: float
    alerts: List[BudgetAlert] = Field(default_factory=list)
    is_exceeded: bool = False
