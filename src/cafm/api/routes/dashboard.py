"""Command Center / Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from cafm.api.dependencies import CurrentUser, require_permission
from cafm.api.schemas.common import APIResponse
from cafm.api.schemas.dashboard import DashboardSummary
from cafm.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Command Center"])

_dashboard_service: DashboardService | None = None


def get_dashboard_service() -> DashboardService:
    if _dashboard_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dashboard service not initialized",
        )
    return _dashboard_service


def set_dashboard_service(svc: DashboardService) -> None:
    global _dashboard_service
    _dashboard_service = svc


@router.get("/summary", response_model=APIResponse)
async def get_dashboard_summary(
    user: CurrentUser = Depends(require_permission("dashboard:read")),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """Get the full Command Center dashboard summary.

    Includes KPIs for assets, work orders, maintenance, costs, and technicians.
    """
    summary = await svc.get_summary()
    return APIResponse(data=summary)


@router.get("/assets/breakdown", response_model=APIResponse)
async def get_asset_breakdown(
    user: CurrentUser = Depends(require_permission("dashboard:read")),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """Get asset breakdown by status, condition, and criticality."""
    breakdown = await svc.get_asset_breakdown()
    return APIResponse(data=breakdown)


@router.get("/work-orders/breakdown", response_model=APIResponse)
async def get_work_order_breakdown(
    user: CurrentUser = Depends(require_permission("dashboard:read")),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """Get work order breakdown by status and priority."""
    breakdown = await svc.get_work_order_breakdown()
    return APIResponse(data=breakdown)


@router.get("/alerts", response_model=APIResponse)
async def get_alerts(
    user: CurrentUser = Depends(require_permission("dashboard:read")),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """Get active alerts for the Command Center.

    Checks for SLA breaches, critical assets, emergency work orders, etc.
    """
    alerts = await svc.get_alerts()
    return APIResponse(data=alerts, message=f"{len(alerts)} active alert(s)")
