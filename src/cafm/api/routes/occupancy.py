"""Occupancy and space utilization API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.gamification import (
    OccupancyResponse, ReservationCreateRequest, ReservationResponse,
    SpaceUtilizationResponse,
)

router = APIRouter(prefix="/occupancy", tags=["Occupancy & Space Utilization"])

_occupancy_service = None


def get_occupancy_service():
    if _occupancy_service is None:
        raise HTTPException(status_code=503, detail="Occupancy service not initialized")
    return _occupancy_service


def set_occupancy_service(svc) -> None:
    global _occupancy_service
    _occupancy_service = svc


# ── Occupancy Data ────────────────────────────────────────────


@router.get("/current", response_model=APIResponse)
async def get_current_occupancy(
    user: CurrentUser,
    building_id: str | None = Query(None), space_id: str | None = Query(None),
    svc=Depends(get_occupancy_service),
):
    """Get current occupancy data for building or space."""
    data = await svc.get_current_occupancy(building_id=building_id, space_id=space_id)
    items = [OccupancyResponse(**d.model_dump()) for d in data]
    return APIResponse(data=items)


@router.get("/utilization", response_model=APIResponse)
async def get_space_utilization(
    user: CurrentUser,
    building_id: str | None = Query(None), space_id: str | None = Query(None),
    period: str = Query("weekly", description="Period: daily, weekly, monthly"),
    svc=Depends(get_occupancy_service),
):
    """Get space utilization metrics."""
    utilization = await svc.get_utilization(
        building_id=building_id, space_id=space_id, period=period,
    )
    items = [SpaceUtilizationResponse(**u.model_dump()) for u in utilization]
    return APIResponse(data=items)


@router.get("/heatmap/{building_id}", response_model=APIResponse)
async def get_occupancy_heatmap(
    building_id: str, user: CurrentUser,
    floor_id: str | None = Query(None),
    svc=Depends(get_occupancy_service),
):
    """Get occupancy heatmap data for a building."""
    heatmap = await svc.get_heatmap(building_id=building_id, floor_id=floor_id)
    return APIResponse(data=heatmap, message="Occupancy heatmap retrieved")


# ── Reservations ──────────────────────────────────────────────


@router.get("/reservations", response_model=APIResponse)
async def list_reservations(
    user: CurrentUser,
    space_id: str | None = Query(None), building_id: str | None = Query(None),
    reservation_status: str | None = Query(None, alias="status"),
    svc=Depends(get_occupancy_service),
):
    filters = {}
    if space_id: filters["space_id"] = space_id
    if building_id: filters["building_id"] = building_id
    if reservation_status: filters["status"] = reservation_status
    reservations, total = await svc.list_reservations(filters=filters or None)
    items = [ReservationResponse(**r.model_dump()) for r in reservations]
    return APIResponse(data={"reservations": items, "total": total})


@router.post("/reservations", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    request: ReservationCreateRequest,
    user: CurrentUser = Depends(require_permission("facilities:write")),
    svc=Depends(get_occupancy_service),
):
    reservation = await svc.create_reservation(request.model_dump(), created_by=user.user_id)
    return APIResponse(
        data=ReservationResponse(**reservation.model_dump()),
        message=f"Reservation '{reservation.reservation_id}' created",
    )


@router.get("/reservations/{reservation_id}", response_model=APIResponse)
async def get_reservation(reservation_id: str, user: CurrentUser, svc=Depends(get_occupancy_service)):
    reservation = await svc.get_reservation(reservation_id)
    if not reservation: raise HTTPException(status_code=404, detail=f"Reservation '{reservation_id}' not found")
    return APIResponse(data=ReservationResponse(**reservation.model_dump()))


@router.post("/reservations/{reservation_id}/cancel", response_model=APIResponse)
async def cancel_reservation(
    reservation_id: str,
    user: CurrentUser = Depends(require_permission("facilities:write")),
    svc=Depends(get_occupancy_service),
):
    cancelled = await svc.cancel_reservation(reservation_id, cancelled_by=user.user_id)
    if not cancelled: raise HTTPException(status_code=404, detail=f"Reservation '{reservation_id}' not found")
    return APIResponse(data=ReservationResponse(**cancelled.model_dump()), message="Reservation cancelled")
