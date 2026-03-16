"""Inspection management API routes (Stories 14, 15, 16)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.inspections import (
    InspectionCreateRequest, InspectionResponse, InspectionUpdateRequest,
)
from cafm.api.schemas.gamification import AssetInsightCreateRequest, AssetInsightResponse

router = APIRouter(prefix="/inspections", tags=["Inspections"])

_inspection_service = None


def get_inspection_service():
    if _inspection_service is None:
        raise HTTPException(status_code=503, detail="Inspection service not initialized")
    return _inspection_service


def set_inspection_service(svc) -> None:
    global _inspection_service
    _inspection_service = svc


@router.get("/", response_model=PaginatedResponse[InspectionResponse])
async def list_inspections(
    pagination: Pagination, user: CurrentUser,
    asset_id: str | None = Query(None), inspector_id: str | None = Query(None),
    inspection_type: str | None = Query(None),
    svc=Depends(get_inspection_service),
):
    filters = {}
    if asset_id: filters["asset_id"] = asset_id
    if inspector_id: filters["inspector_id"] = inspector_id
    if inspection_type: filters["inspection_type"] = inspection_type
    reports, total = await svc.list_inspections(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [InspectionResponse(**r.model_dump()) for r in reports]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    request: InspectionCreateRequest,
    user: CurrentUser = Depends(require_permission("inspections:write")),
    svc=Depends(get_inspection_service),
):
    """Create an inspection report with voice notes, photos, and text (Story 14)."""
    report = await svc.create_inspection(request.model_dump(), inspector_id=user.user_id)
    return APIResponse(data=InspectionResponse(**report.model_dump()), message=f"Inspection '{report.report_id}' created")


@router.get("/prefill", response_model=APIResponse)
async def get_prefilled_data(
    asset_id: str = Query(...), user: CurrentUser = Depends(require_permission("inspections:write")),
    svc=Depends(get_inspection_service),
):
    """Get pre-filled inspection data (Story 15a: 50% pre-filled config)."""
    prefilled = await svc.get_prefilled_data(asset_id, user.user_id)
    return APIResponse(data=prefilled, message="Pre-filled data ready")


@router.get("/{report_id}", response_model=APIResponse)
async def get_inspection(report_id: str, user: CurrentUser, svc=Depends(get_inspection_service)):
    report = await svc.get_inspection(report_id)
    if not report: raise HTTPException(status_code=404, detail=f"Inspection '{report_id}' not found")
    return APIResponse(data=InspectionResponse(**report.model_dump()))


@router.patch("/{report_id}", response_model=APIResponse)
async def update_inspection(
    report_id: str, request: InspectionUpdateRequest,
    user: CurrentUser = Depends(require_permission("inspections:write")),
    svc=Depends(get_inspection_service),
):
    updated = await svc.update_inspection(report_id, request.model_dump(exclude_unset=True))
    if not updated: raise HTTPException(status_code=404, detail=f"Inspection '{report_id}' not found")
    return APIResponse(data=InspectionResponse(**updated.model_dump()))


@router.post("/{report_id}/classify", response_model=APIResponse)
async def classify_inspection(
    report_id: str,
    user: CurrentUser = Depends(require_permission("inspections:write")),
    svc=Depends(get_inspection_service),
):
    """AI-classify an inspection and trigger actions (Story 15b)."""
    result = await svc.classify_inspection(report_id)
    return APIResponse(data=result, message="Inspection classified")


# ── Asset Insights via QR Scan (Story 16) ──────────────────────

@router.post("/insights", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def submit_asset_insight(
    request: AssetInsightCreateRequest,
    user: CurrentUser = Depends(require_permission("inspections:write")),
    svc=Depends(get_inspection_service),
):
    """Submit a technical insight after scanning an asset QR code (Story 16)."""
    insight = await svc.submit_asset_insight(
        technician_id=user.user_id, asset_id=request.asset_id,
        insight_text=request.insight_text, qr_code=request.qr_code,
        voice_note_url=request.voice_note_url, photo_urls=request.photo_urls,
    )
    if not insight: raise HTTPException(status_code=503, detail="Insight repository not configured")
    return APIResponse(data=AssetInsightResponse(**insight.model_dump()), message="Insight submitted and classified")


@router.get("/insights/asset/{asset_id}", response_model=APIResponse)
async def get_asset_insights(asset_id: str, user: CurrentUser, svc=Depends(get_inspection_service)):
    insights, total = await svc.get_asset_insights(asset_id)
    items = [AssetInsightResponse(**i.model_dump()) for i in insights]
    return APIResponse(data={"insights": items, "total": total})
