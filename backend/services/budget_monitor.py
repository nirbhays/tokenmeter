"""
Budget Monitor — checks spend against budgets and triggers alerts.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from backend.config import get_settings
from backend.models.budget import (
    AlertChannel,
    AlertSeverity,
    Budget,
    BudgetAlert,
    BudgetPeriod,
    BudgetStatus,
    BudgetThreshold,
)

logger = logging.getLogger(__name__)


class BudgetMonitor:
    """Monitors spend against configured budgets and creates alerts."""

    def __init__(self):
        self._budgets: Dict[str, Budget] = {}  # budget_id → Budget
        self._alerts: List[BudgetAlert] = []
        self._running = False
        self._check_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        settings = get_settings()
        self._check_task = asyncio.create_task(
            self._monitor_loop(settings.budget_check_interval_seconds)
        )
        logger.info("Budget monitor started")

    async def stop(self) -> None:
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("Budget monitor stopped")

    def add_budget(self, budget: Budget) -> None:
        """Register a budget for monitoring."""
        self._budgets[budget.id] = budget
        logger.info("Budget added: %s ($%.2f %s)", budget.name, budget.amount_usd, budget.period.value)

    def remove_budget(self, budget_id: str) -> None:
        self._budgets.pop(budget_id, None)

    def get_budget(self, budget_id: str) -> Optional[Budget]:
        return self._budgets.get(budget_id)

    def list_budgets(self, org_id: str) -> List[Budget]:
        return [b for b in self._budgets.values() if b.org_id == org_id]

    def record_spend(self, org_id: str, amount_usd: float, *, team: Optional[str] = None,
                     feature: Optional[str] = None, model: Optional[str] = None,
                     provider: Optional[str] = None) -> List[BudgetAlert]:
        """Record spend and return any triggered alerts."""
        triggered = []

        for budget in self._budgets.values():
            if budget.org_id != org_id or not budget.enabled:
                continue
            # Check scope filters
            if budget.team and budget.team != team:
                continue
            if budget.feature and budget.feature != feature:
                continue
            if budget.model and budget.model != model:
                continue
            if budget.provider and budget.provider != provider:
                continue

            budget.current_spend_usd += amount_usd
            utilization = (budget.current_spend_usd / budget.amount_usd * 100) if budget.amount_usd > 0 else 0

            # Check thresholds
            for threshold in budget.thresholds:
                if threshold.notified:
                    continue
                if utilization >= threshold.percentage:
                    alert = BudgetAlert(
                        budget_id=budget.id,
                        org_id=org_id,
                        threshold_percentage=threshold.percentage,
                        severity=threshold.severity,
                        current_spend_usd=budget.current_spend_usd,
                        budget_amount_usd=budget.amount_usd,
                        utilization_percentage=round(utilization, 1),
                        message=self._format_alert_message(budget, threshold, utilization),
                        channels_notified=threshold.channels,
                    )
                    threshold.notified = True
                    threshold.notified_at = datetime.utcnow()
                    self._alerts.append(alert)
                    triggered.append(alert)
                    logger.warning("Budget alert: %s", alert.message)

        return triggered

    def check_hard_limit(self, org_id: str, *, team: Optional[str] = None,
                         feature: Optional[str] = None) -> Optional[Budget]:
        """Check if any hard-limit budget is exceeded. Returns the exceeded budget or None."""
        for budget in self._budgets.values():
            if budget.org_id != org_id or not budget.enabled or not budget.hard_limit:
                continue
            if budget.team and budget.team != team:
                continue
            if budget.feature and budget.feature != feature:
                continue
            if budget.current_spend_usd >= budget.amount_usd:
                return budget
        return None

    def get_budget_status(self, budget_id: str) -> Optional[BudgetStatus]:
        budget = self._budgets.get(budget_id)
        if not budget:
            return None

        utilization = (budget.current_spend_usd / budget.amount_usd * 100) if budget.amount_usd > 0 else 0
        remaining = max(0, budget.amount_usd - budget.current_spend_usd)
        alerts = [a for a in self._alerts if a.budget_id == budget_id]

        # Simple linear projection
        now = datetime.utcnow()
        period_days = {"daily": 1, "weekly": 7, "monthly": 30}
        total_days = period_days.get(budget.period.value, 30)
        days_elapsed = max(1, (now - budget.period_start).days) if budget.period_start else 1
        daily_rate = budget.current_spend_usd / days_elapsed
        projected = daily_rate * total_days

        return BudgetStatus(
            budget=budget,
            utilization_percentage=round(utilization, 1),
            remaining_usd=round(remaining, 4),
            projected_end_of_period_usd=round(projected, 2),
            alerts=alerts,
            is_exceeded=budget.current_spend_usd >= budget.amount_usd,
        )

    def reset_period(self, budget_id: str) -> None:
        """Reset a budget's spend counter for a new period."""
        budget = self._budgets.get(budget_id)
        if budget:
            budget.current_spend_usd = 0.0
            budget.period_start = datetime.utcnow()
            for t in budget.thresholds:
                t.notified = False
                t.notified_at = None

    async def _monitor_loop(self, interval: int) -> None:
        """Periodic check loop."""
        while self._running:
            await asyncio.sleep(interval)
            # Check if any budgets need period resets
            now = datetime.utcnow()
            for budget in self._budgets.values():
                if budget.period_end and now >= budget.period_end:
                    self.reset_period(budget.id)
                    # Set new period end
                    if budget.period == BudgetPeriod.daily:
                        budget.period_end = now + timedelta(days=1)
                    elif budget.period == BudgetPeriod.weekly:
                        budget.period_end = now + timedelta(weeks=1)
                    else:
                        budget.period_end = now + timedelta(days=30)

    def _format_alert_message(self, budget: Budget, threshold: BudgetThreshold, utilization: float) -> str:
        scope = budget.name
        if budget.team:
            scope += f" (team: {budget.team})"
        if budget.feature:
            scope += f" (feature: {budget.feature})"

        return (
            f"🚨 Budget Alert: {scope} has reached {utilization:.1f}% "
            f"(${budget.current_spend_usd:.2f} / ${budget.amount_usd:.2f}) — "
            f"severity: {threshold.severity.value}"
        )

    @property
    def recent_alerts(self) -> List[BudgetAlert]:
        return self._alerts[-100:]  # Keep last 100 alerts


# Module-level singleton
_monitor: Optional[BudgetMonitor] = None


def get_budget_monitor() -> BudgetMonitor:
    global _monitor
    if _monitor is None:
        _monitor = BudgetMonitor()
    return _monitor
