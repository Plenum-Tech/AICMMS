"""Maintenance and PPM management API routes (Story 3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.maintenance import (
    MaintenanceScheduleCreateRequest, MaintenanceScheduleResponse, PPMInsightResponse,
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance & PPM"])

_maintenance_service = None


def get_maintenance_service():
    if _maintenance_service is None:
        raise HTTPException(status_code=503, detail="Maintenance service not initialized")
    return _maintenance_service


def set_maintenance_service(svc) -> None:
    global _maintenance_service
    _maintenance_service = svc


# ── PPM Schedules ──────────────────────────────────────────────


@router.get("/schedules", response_model=PaginatedResponse[MaintenanceScheduleResponse])
async def list_schedules(
    pagination: Pagination, user: CurrentUser,
    asset_id: str | None = Query(None), is_active: bool | None = Query(None),
    svc=Depends(get_maintenance_service),
):
    filters = {}
    if asset_id: filters["asset_id"] = asset_id
    if is_active is not None: filters["is_active"] = is_active
    schedules, total = await svc.list_schedules(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [MaintenanceScheduleResponse(**s.model_dump()) for s in schedules]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/schedules", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    request: MaintenanceScheduleCreateRequest,
    user: CurrentUser = Depends(require_permission("maintenance:write")),
    svc=Depends(get_maintenance_service),
):
    schedule = await svc.create_schedule(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=MaintenanceScheduleResponse(**schedule.model_dump()), message=f"Schedule '{schedule.schedule_id}' created")


@router.get("/schedules/upcoming", response_model=APIResponse)
async def get_upcoming_ppm(
    days_ahead: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(require_permission("maintenance:read")),
    svc=Depends(get_maintenance_service),
):
    """Get PPM schedules due within N days (Story 3)."""
    upcoming = await svc.get_upcoming_ppm(days_ahead=days_ahead)
    items = [MaintenanceScheduleResponse(**s.model_dump()) for s in upcoming]
    return APIResponse(data=items, message=f"{len(items)} upcoming schedule(s) in next {days_ahead} days")


@router.get("/schedules/overdue", response_model=APIResponse)
async def get_overdue_ppm(
    user: CurrentUser = Depends(require_permission("maintenance:read")),
    svc=Depends(get_maintenance_service),
):
    """Get overdue PPM schedules (Story 3)."""
    overdue = await svc.get_overdue_ppm()
    items = [MaintenanceScheduleResponse(**s.model_dump()) for s in overdue]
    return APIResponse(data=items, message=f"{len(items)} overdue schedule(s)")


@router.get("/schedules/{schedule_id}", response_model=APIResponse)
async def get_schedule(schedule_id: str, user: CurrentUser, svc=Depends(get_maintenance_service)):
    schedule = await svc.get_schedule(schedule_id)
    if not schedule: raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found")
    return APIResponse(data=MaintenanceScheduleResponse(**schedule.model_dump()))


@router.patch("/schedules/{schedule_id}", response_model=APIResponse)
async def update_schedule(
    schedule_id: str, request: MaintenanceScheduleCreateRequest,
    user: CurrentUser = Depends(require_permission("maintenance:write")),
    svc=Depends(get_maintenance_service),
):
    updated = await svc.update_schedule(schedule_id, request.model_dump(exclude_unset=True))
    if not updated: raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found")
    return APIResponse(data=MaintenanceScheduleResponse(**updated.model_dump()))


# ── PPM Insights (AI-powered) ────────────────────────────────


@router.get("/insights/{asset_id}", response_model=APIResponse)
async def get_ppm_insights(
    asset_id: str,
    user: CurrentUser = Depends(require_permission("maintenance:read")),
    svc=Depends(get_maintenance_service),
):
    """Get AI-generated PPM insights for an asset (Story 3)."""
    insights = await svc.generate_ppm_insights(asset_id)
    return APIResponse(data=insights, message="PPM insights generated")


# ── Maintenance Logs ──────────────────────────────────────────


@router.get("/logs", response_model=APIResponse)
async def list_maintenance_logs(
    user: CurrentUser,
    asset_id: str | None = Query(None), schedule_id: str | None = Query(None),
    svc=Depends(get_maintenance_service),
):
    filters = {}
    if asset_id: filters["asset_id"] = asset_id
    if schedule_id: filters["schedule_id"] = schedule_id
    logs, total = await svc.list_maintenance_logs(filters=filters or None)
    return APIResponse(data={"logs": [lg.model_dump() for lg in logs], "total": total})


# ── Failure Modes ─────────────────────────────────────────────


@router.get("/failure-modes", response_model=APIResponse)
async def list_failure_modes(
    user: CurrentUser,
    asset_category: str | None = Query(None),
    svc=Depends(get_maintenance_service),
):
    modes, total = await svc.list_failure_modes(asset_category=asset_category)
    return APIResponse(data={"failure_modes": [m.model_dump() for m in modes], "total": total})
