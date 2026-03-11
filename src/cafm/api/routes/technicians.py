"""Technician / manpower management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.technicians import (
    TechnicianCreateRequest,
    TechnicianResponse,
    TechnicianRoutingResponse,
    TechnicianUpdateRequest,
)
from cafm.services.technician_service import TechnicianService

router = APIRouter(prefix="/technicians", tags=["Technicians"])

_technician_service: TechnicianService | None = None


def get_technician_service() -> TechnicianService:
    if _technician_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Technician service not initialized",
        )
    return _technician_service


def set_technician_service(svc: TechnicianService) -> None:
    global _technician_service
    _technician_service = svc


@router.get("/", response_model=PaginatedResponse[TechnicianResponse])
async def list_technicians(
    pagination: Pagination,
    user: CurrentUser,
    is_available: bool | None = Query(None),
    vendor_id: str | None = Query(None),
    role: str | None = Query(None),
    svc: TechnicianService = Depends(get_technician_service),
):
    """List technicians with filtering and pagination."""
    filters: dict = {}
    if is_available is not None:
        filters["is_available"] = is_available
    if vendor_id:
        filters["vendor_id"] = vendor_id
    if role:
        filters["role"] = role

    technicians, total = await svc.list_technicians(
        filters=filters or None,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    items = [TechnicianResponse(**t.model_dump()) for t in technicians]
    return PaginatedResponse.create(
        items=items, total=total,
        page=pagination.page, page_size=pagination.page_size,
    )


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_technician(
    request: TechnicianCreateRequest,
    user: CurrentUser = Depends(require_permission("technicians:write")),
    svc: TechnicianService = Depends(get_technician_service),
):
    """Create a new technician record."""
    tech = await svc.create_technician(
        data=request.model_dump(), created_by=user.user_id,
    )
    return APIResponse(
        data=TechnicianResponse(**tech.model_dump()),
        message=f"Technician '{tech.technician_id}' created",
    )


@router.get("/available", response_model=APIResponse)
async def list_available_technicians(
    user: CurrentUser,
    skill_codes: str | None = Query(None, description="Comma-separated skill codes"),
    svc: TechnicianService = Depends(get_technician_service),
):
    """List all currently available technicians."""
    skills = skill_codes.split(",") if skill_codes else None
    techs = await svc.get_available_technicians(skill_codes=skills)
    items = [TechnicianResponse(**t.model_dump()) for t in techs]
    return APIResponse(data=items)


@router.post("/recommend", response_model=APIResponse)
async def recommend_technician(
    required_skills: list[str] = Query(..., description="Required skill codes"),
    building_id: str | None = Query(None),
    priority: str = Query("medium"),
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: TechnicianService = Depends(get_technician_service),
):
    """Get AI-recommended technicians for a work order.

    Per AICMMS spec: auto-route work orders to the right technician
    based on availability, distance, expertise, and workload.
    """
    recommendations = await svc.recommend_technician(
        required_skills=required_skills,
        building_id=building_id,
        priority=priority,
    )
    items = [TechnicianRoutingResponse(**r) for r in recommendations]
    return APIResponse(data=items, message=f"Found {len(items)} recommendation(s)")


@router.get("/{technician_id}", response_model=APIResponse)
async def get_technician(
    technician_id: str,
    user: CurrentUser,
    svc: TechnicianService = Depends(get_technician_service),
):
    """Get a single technician by ID."""
    tech = await svc.get_technician(technician_id)
    if tech is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician '{technician_id}' not found",
        )
    return APIResponse(data=TechnicianResponse(**tech.model_dump()))


@router.patch("/{technician_id}", response_model=APIResponse)
async def update_technician(
    technician_id: str,
    request: TechnicianUpdateRequest,
    user: CurrentUser = Depends(require_permission("technicians:write")),
    svc: TechnicianService = Depends(get_technician_service),
):
    """Update a technician record."""
    updated = await svc.update_technician(
        technician_id, request.model_dump(exclude_unset=True), updated_by=user.user_id,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician '{technician_id}' not found",
        )
    return APIResponse(data=TechnicianResponse(**updated.model_dump()))


@router.post("/{technician_id}/award-points", response_model=APIResponse)
async def award_gamification_points(
    technician_id: str,
    points: int = Query(..., ge=1, le=1000),
    reason: str = Query("task_completion"),
    user: CurrentUser = Depends(require_permission("technicians:write")),
    svc: TechnicianService = Depends(get_technician_service),
):
    """Award gamification points to a technician.

    Per AICMMS spec: gamified points for inputs and impact rewards.
    """
    tech = await svc.award_points(technician_id, points, reason)
    if tech is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician '{technician_id}' not found",
        )
    return APIResponse(
        data=TechnicianResponse(**tech.model_dump()),
        message=f"Awarded {points} points for: {reason}",
    )
