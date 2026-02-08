"""Tests for budget monitoring."""

import pytest

from backend.models.budget import (
    AlertChannel,
    AlertSeverity,
    Budget,
    BudgetPeriod,
    BudgetThreshold,
)
from backend.services.budget_monitor import BudgetMonitor


@pytest.fixture
def monitor():
    return BudgetMonitor()


@pytest.fixture
def sample_budget():
    return Budget(
        org_id="test_org",
        name="Monthly AI Spend",
        amount_usd=100.0,
        period=BudgetPeriod.monthly,
        thresholds=[
            BudgetThreshold(percentage=50.0, severity=AlertSeverity.info, channels=[AlertChannel.slack]),
            BudgetThreshold(percentage=80.0, severity=AlertSeverity.warning, channels=[AlertChannel.slack]),
            BudgetThreshold(percentage=100.0, severity=AlertSeverity.critical, channels=[AlertChannel.slack, AlertChannel.email]),
        ],
    )


class TestBudgetMonitor:
    def test_add_budget(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        assert len(monitor.list_budgets("test_org")) == 1

    def test_record_spend_no_alert(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        alerts = monitor.record_spend("test_org", 10.0)
        assert len(alerts) == 0
        assert sample_budget.current_spend_usd == 10.0

    def test_50_percent_alert(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        alerts = monitor.record_spend("test_org", 55.0)
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.info
        assert alerts[0].utilization_percentage == 55.0

    def test_80_percent_alert(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        monitor.record_spend("test_org", 55.0)  # triggers 50%
        alerts = monitor.record_spend("test_org", 30.0)  # total: 85 → triggers 80%
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.warning

    def test_100_percent_alert(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        alerts = monitor.record_spend("test_org", 105.0)
        # Should trigger all three thresholds
        assert len(alerts) == 3
        severities = {a.severity for a in alerts}
        assert AlertSeverity.info in severities
        assert AlertSeverity.warning in severities
        assert AlertSeverity.critical in severities

    def test_no_duplicate_alerts(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        monitor.record_spend("test_org", 55.0)  # triggers 50%
        alerts = monitor.record_spend("test_org", 5.0)  # 60%, 50% already notified
        assert len(alerts) == 0

    def test_hard_limit_check(self, monitor):
        budget = Budget(
            org_id="test_org",
            name="Hard Limit",
            amount_usd=50.0,
            period=BudgetPeriod.monthly,
            hard_limit=True,
        )
        monitor.add_budget(budget)
        monitor.record_spend("test_org", 60.0)

        exceeded = monitor.check_hard_limit("test_org")
        assert exceeded is not None
        assert exceeded.name == "Hard Limit"

    def test_hard_limit_not_exceeded(self, monitor):
        budget = Budget(
            org_id="test_org",
            name="Hard Limit",
            amount_usd=100.0,
            hard_limit=True,
        )
        monitor.add_budget(budget)
        monitor.record_spend("test_org", 50.0)

        assert monitor.check_hard_limit("test_org") is None

    def test_team_scoped_budget(self, monitor):
        budget = Budget(
            org_id="test_org",
            name="Search Team Budget",
            team="search",
            amount_usd=50.0,
        )
        monitor.add_budget(budget)

        # Spend for different team — should not affect
        monitor.record_spend("test_org", 100.0, team="chatbot")
        assert budget.current_spend_usd == 0.0

        # Spend for matching team
        monitor.record_spend("test_org", 30.0, team="search")
        assert budget.current_spend_usd == 30.0

    def test_reset_period(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        monitor.record_spend("test_org", 80.0)
        assert sample_budget.current_spend_usd == 80.0

        monitor.reset_period(sample_budget.id)
        assert sample_budget.current_spend_usd == 0.0
        # Thresholds should be reset too
        assert all(not t.notified for t in sample_budget.thresholds)

    def test_budget_status(self, monitor, sample_budget):
        monitor.add_budget(sample_budget)
        monitor.record_spend("test_org", 65.0)

        status = monitor.get_budget_status(sample_budget.id)
        assert status is not None
        assert status.utilization_percentage == 65.0
        assert status.remaining_usd == 35.0
        assert status.is_exceeded is False
