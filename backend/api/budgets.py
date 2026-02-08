"""
Budget management endpoints.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request

from backend.models.budget import (
    Budget,
    BudgetCreate,
    BudgetStatus,
    BudgetUpdate,
)
from backend.services.budget_monitor import get_budget_monitor

router = APIRouter(prefix="/api/budgets", tags=["Budgets"])


@router.get("/", response_model=List[Budget])
async def list_budgets(request: Request):
    """List all budgets for the current organization."""
    org_id = getattr(request.state, "org_id", "default")
    monitor = get_budget_monitor()
    return monitor.list_budgets(org_id)


@router.post("/", response_model=Budget)
async def create_budget(body: BudgetCreate, request: Request):
    """Create a new budget."""
    org_id = getattr(request.state, "org_id", "default")
    monitor = get_budget_monitor()

    budget = Budget(
        org_id=org_id,
        name=body.name,
        team=body.team,
        feature=body.feature,
        model=body.model,
        provider=body.provider,
        amount_usd=body.amount_usd,
        period=body.period,
        hard_limit=body.hard_limit,
    )
    if body.thresholds:
        budget.thresholds = body.thresholds

    monitor.add_budget(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetStatus)
async def get_budget_status(budget_id: str, request: Request):
    """Get current status of a budget."""
    monitor = get_budget_monitor()
    status = monitor.get_budget_status(budget_id)
    if not status:
        raise HTTPException(status_code=404, detail="Budget not found")
    return status


@router.put("/{budget_id}", response_model=Budget)
async def update_budget(budget_id: str, body: BudgetUpdate, request: Request):
    """Update a budget."""
    monitor = get_budget_monitor()
    budget = monitor.get_budget(budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if body.name is not None:
        budget.name = body.name
    if body.amount_usd is not None:
        budget.amount_usd = body.amount_usd
    if body.period is not None:
        budget.period = body.period
    if body.thresholds is not None:
        budget.thresholds = body.thresholds
    if body.hard_limit is not None:
        budget.hard_limit = body.hard_limit
    if body.enabled is not None:
        budget.enabled = body.enabled

    return budget


@router.delete("/{budget_id}")
async def delete_budget(budget_id: str, request: Request):
    """Delete a budget."""
    monitor = get_budget_monitor()
    monitor.remove_budget(budget_id)
    return {"status": "deleted", "budget_id": budget_id}


@router.get("/{budget_id}/alerts")
async def get_budget_alerts(budget_id: str, request: Request):
    """Get recent alerts for a budget."""
    monitor = get_budget_monitor()
    alerts = [a for a in monitor.recent_alerts if a.budget_id == budget_id]
    return {"data": [a.model_dump() for a in alerts]}


@router.post("/{budget_id}/reset")
async def reset_budget(budget_id: str, request: Request):
    """Reset a budget's current spend to zero."""
    monitor = get_budget_monitor()
    monitor.reset_period(budget_id)
    return {"status": "reset", "budget_id": budget_id}
