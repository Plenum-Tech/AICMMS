"""Facilities management API routes — buildings, floors, spaces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.facilities import BuildingCreateRequest, BuildingResponse, SpaceResponse

router = APIRouter(prefix="/facilities", tags=["Facilities"])

_facility_service = None


def get_facility_service():
    if _facility_service is None:
        raise HTTPException(status_code=503, detail="Facility service not initialized")
    return _facility_service


def set_facility_service(svc) -> None:
    global _facility_service
    _facility_service = svc


@router.get("/buildings", response_model=PaginatedResponse[BuildingResponse])
async def list_buildings(
    pagination: Pagination, user: CurrentUser,
    building_status: str | None = Query(None, alias="status"),
    city: str | None = Query(None),
    svc=Depends(get_facility_service),
):
    filters = {}
    if building_status: filters["status"] = building_status
    if city: filters["city"] = city
    buildings, total = await svc.list_buildings(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [BuildingResponse(**b.model_dump()) for b in buildings]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/buildings", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_building(
    request: BuildingCreateRequest,
    user: CurrentUser = Depends(require_permission("facilities:write")),
    svc=Depends(get_facility_service),
):
    building = await svc.create_building(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=BuildingResponse(**building.model_dump()), message=f"Building '{building.building_id}' created")


@router.get("/buildings/{building_id}", response_model=APIResponse)
async def get_building(building_id: str, user: CurrentUser, svc=Depends(get_facility_service)):
    building = await svc.get_building(building_id)
    if not building: raise HTTPException(status_code=404, detail=f"Building '{building_id}' not found")
    return APIResponse(data=BuildingResponse(**building.model_dump()))


@router.get("/buildings/{building_id}/hierarchy", response_model=APIResponse)
async def get_building_hierarchy(building_id: str, user: CurrentUser, svc=Depends(get_facility_service)):
    hierarchy = await svc.get_building_hierarchy(building_id)
    if not hierarchy: raise HTTPException(status_code=404, detail=f"Building '{building_id}' not found")
    return APIResponse(data=hierarchy)


@router.get("/buildings/{building_id}/floors", response_model=APIResponse)
async def list_floors(building_id: str, user: CurrentUser, svc=Depends(get_facility_service)):
    floors, total = await svc.list_floors(building_id)
    return APIResponse(data=[f.model_dump() for f in floors])


@router.get("/spaces", response_model=PaginatedResponse[SpaceResponse])
async def list_spaces(
    pagination: Pagination, user: CurrentUser,
    building_id: str | None = Query(None), floor_id: str | None = Query(None),
    space_type: str | None = Query(None),
    svc=Depends(get_facility_service),
):
    filters = {}
    if building_id: filters["building_id"] = building_id
    if floor_id: filters["floor_id"] = floor_id
    if space_type: filters["space_type"] = space_type
    spaces, total = await svc.list_spaces(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [SpaceResponse(**s.model_dump()) for s in spaces]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)
