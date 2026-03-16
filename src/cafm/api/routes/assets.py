"""Asset management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.assets import (
    AssetCreateRequest,
    AssetResponse,
    AssetUpdateRequest,
)
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["Assets"])

# In production, AssetService would be injected via Depends().
# For now, routes accept it will be wired in the app factory.
_asset_service: AssetService | None = None


def get_asset_service() -> AssetService:
    if _asset_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Asset service not initialized",
        )
    return _asset_service


def set_asset_service(svc: AssetService) -> None:
    global _asset_service
    _asset_service = svc


@router.get("/", response_model=PaginatedResponse[AssetResponse])
async def list_assets(
    pagination: Pagination,
    user: CurrentUser,
    facility_id: str | None = Query(None),
    category: str | None = Query(None),
    asset_status: str | None = Query(None, alias="status"),
    condition: str | None = Query(None),
    criticality: str | None = Query(None),
    search: str | None = Query(None),
    svc: AssetService = Depends(get_asset_service),
):
    """List assets with filtering and pagination."""
    filters: dict = {}
    if facility_id:
        filters["facility_id"] = facility_id
    if category:
        filters["category"] = category
    if asset_status:
        filters["status"] = asset_status
    if condition:
        filters["condition"] = condition
    if criticality:
        filters["criticality"] = criticality

    assets, total = await svc.list_assets(
        filters=filters or None,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    items = [AssetResponse(**a.model_dump()) for a in assets]
    return PaginatedResponse.create(
        items=items, total=total,
        page=pagination.page, page_size=pagination.page_size,
    )


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    request: AssetCreateRequest,
    user: CurrentUser = Depends(require_permission("assets:write")),
    svc: AssetService = Depends(get_asset_service),
):
    """Create a new asset with auto-generated QR code."""
    asset = await svc.create_asset(
        data=request.model_dump(), created_by=user.user_id,
    )
    return APIResponse(
        data=AssetResponse(**asset.model_dump()),
        message=f"Asset '{asset.asset_id}' created with QR code: {asset.qr_code}",
    )


@router.get("/{asset_id}", response_model=APIResponse)
async def get_asset(
    asset_id: str,
    user: CurrentUser,
    svc: AssetService = Depends(get_asset_service),
):
    """Get a single asset by ID."""
    asset = await svc.get_asset(asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found",
        )
    return APIResponse(data=AssetResponse(**asset.model_dump()))


@router.patch("/{asset_id}", response_model=APIResponse)
async def update_asset(
    asset_id: str,
    request: AssetUpdateRequest,
    user: CurrentUser = Depends(require_permission("assets:write")),
    svc: AssetService = Depends(get_asset_service),
):
    """Update an asset."""
    updated = await svc.update_asset(
        asset_id, request.model_dump(exclude_unset=True), updated_by=user.user_id,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found",
        )
    return APIResponse(data=AssetResponse(**updated.model_dump()), message="Asset updated")


@router.delete("/{asset_id}", response_model=APIResponse)
async def delete_asset(
    asset_id: str,
    user: CurrentUser = Depends(require_permission("assets:delete")),
    svc: AssetService = Depends(get_asset_service),
):
    """Soft-delete an asset."""
    deleted = await svc.delete_asset(asset_id, deleted_by=user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found",
        )
    return APIResponse(message=f"Asset '{asset_id}' deleted")


@router.get("/{asset_id}/qr")
async def get_asset_qr(
    asset_id: str,
    user: CurrentUser,
    svc: AssetService = Depends(get_asset_service),
):
    """Get the QR code data for an asset.

    In production, this would return a QR code image.
    """
    asset = await svc.get_asset(asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found",
        )
    return APIResponse(
        data={
            "asset_id": asset.asset_id,
            "qr_code": asset.qr_code,
            "qr_code_url": asset.qr_code_url,
        }
    )


@router.get("/stats/summary", response_model=APIResponse)
async def asset_stats(
    user: CurrentUser,
    svc: AssetService = Depends(get_asset_service),
):
    """Get asset statistics summary."""
    total = await svc.get_asset_count()
    active = await svc.get_asset_count(filters={"status": "active"})
    critical = await svc.get_asset_count(filters={"criticality": "critical"})

    return APIResponse(data={
        "total": total,
        "active": active,
        "critical": critical,
    })
