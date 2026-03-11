"""Work order management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.work_orders import (
    WorkOrderAdHocRequest,
    WorkOrderCreateRequest,
    WorkOrderResponse,
    WorkOrderUpdateRequest,
)
from cafm.domain.enums import WorkOrderStatus
from cafm.services.work_order_service import WorkOrderService

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])

_work_order_service: WorkOrderService | None = None


def get_work_order_service() -> WorkOrderService:
    if _work_order_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Work order service not initialized",
        )
    return _work_order_service


def set_work_order_service(svc: WorkOrderService) -> None:
    global _work_order_service
    _work_order_service = svc


@router.get("/", response_model=PaginatedResponse[WorkOrderResponse])
async def list_work_orders(
    pagination: Pagination,
    user: CurrentUser,
    wo_status: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    work_order_type: str | None = Query(None),
    building_id: str | None = Query(None),
    asset_id: str | None = Query(None),
    assigned_to: str | None = Query(None),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """List work orders with filtering and pagination."""
    filters: dict = {}
    if wo_status:
        filters["status"] = wo_status
    if priority:
        filters["priority"] = priority
    if work_order_type:
        filters["work_order_type"] = work_order_type
    if building_id:
        filters["building_id"] = building_id
    if asset_id:
        filters["asset_id"] = asset_id
    if assigned_to:
        filters["assigned_to"] = assigned_to

    work_orders, total = await svc.list_work_orders(
        filters=filters or None,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    items = [WorkOrderResponse(**wo.model_dump()) for wo in work_orders]
    return PaginatedResponse.create(
        items=items, total=total,
        page=pagination.page, page_size=pagination.page_size,
    )


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    request: WorkOrderCreateRequest,
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Create a new work order."""
    wo = await svc.create_work_order(
        data=request.model_dump(), created_by=user.user_id,
    )
    return APIResponse(
        data=WorkOrderResponse(**wo.model_dump()),
        message=f"Work order '{wo.work_order_id}' created",
    )


@router.post("/adhoc", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_adhoc_work_order(
    request: WorkOrderAdHocRequest,
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Create an ad-hoc work order from text or voice note.

    Per AICMMS spec: users can create work orders via text/voice notes
    through the query interface on mobile.
    """
    wo = await svc.create_adhoc_work_order(
        text=request.text,
        building_id=request.building_id,
        asset_id=request.asset_id,
        priority=request.priority,
        requested_by=user.user_id,
    )
    return APIResponse(
        data=WorkOrderResponse(**wo.model_dump()),
        message=f"Ad-hoc work order '{wo.work_order_id}' created",
    )


@router.get("/{work_order_id}", response_model=APIResponse)
async def get_work_order(
    work_order_id: str,
    user: CurrentUser,
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Get a single work order."""
    wo = await svc.get_work_order(work_order_id)
    if wo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work order '{work_order_id}' not found",
        )
    return APIResponse(data=WorkOrderResponse(**wo.model_dump()))


@router.patch("/{work_order_id}", response_model=APIResponse)
async def update_work_order(
    work_order_id: str,
    request: WorkOrderUpdateRequest,
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Update a work order."""
    updated = await svc.update_work_order(
        work_order_id, request.model_dump(exclude_unset=True), updated_by=user.user_id,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work order '{work_order_id}' not found",
        )
    return APIResponse(data=WorkOrderResponse(**updated.model_dump()), message="Work order updated")


@router.post("/{work_order_id}/transition", response_model=APIResponse)
async def transition_work_order_status(
    work_order_id: str,
    new_status: WorkOrderStatus = Query(...),
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Transition a work order to a new status with validation."""
    try:
        wo = await svc.transition_status(work_order_id, new_status, by=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if wo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work order '{work_order_id}' not found",
        )
    return APIResponse(
        data=WorkOrderResponse(**wo.model_dump()),
        message=f"Status transitioned to {new_status}",
    )


@router.post("/{work_order_id}/assign", response_model=APIResponse)
async def assign_work_order(
    work_order_id: str,
    technician_id: str = Query(...),
    user: CurrentUser = Depends(require_permission("work_orders:write")),
    svc: WorkOrderService = Depends(get_work_order_service),
):
    """Assign a work order to a technician."""
    wo = await svc.assign_work_order(work_order_id, technician_id, by=user.user_id)
    if wo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work order '{work_order_id}' not found",
        )
    return APIResponse(
        data=WorkOrderResponse(**wo.model_dump()),
        message=f"Assigned to technician {technician_id}",
    )
