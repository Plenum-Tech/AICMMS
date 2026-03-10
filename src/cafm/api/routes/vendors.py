"""Vendor and contract management API routes (Story 11)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.vendors import (
    ContractCreateRequest, ContractResponse, SLACreateRequest, SLAResponse,
    VendorCreateRequest, VendorResponse, VendorUpdateRequest,
)

router = APIRouter(prefix="/vendors", tags=["Vendors & Contracts"])

# Service injection placeholder — wired at app startup
_vendor_service = None


def get_vendor_service():
    if _vendor_service is None:
        raise HTTPException(status_code=503, detail="Vendor service not initialized")
    return _vendor_service


def set_vendor_service(svc) -> None:
    global _vendor_service
    _vendor_service = svc


@router.get("/", response_model=PaginatedResponse[VendorResponse])
async def list_vendors(
    pagination: Pagination, user: CurrentUser,
    vendor_type: str | None = Query(None), is_active: bool | None = Query(None),
    svc=Depends(get_vendor_service),
):
    filters = {}
    if vendor_type: filters["vendor_type"] = vendor_type
    if is_active is not None: filters["is_active"] = is_active
    vendors, total = await svc.list_vendors(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [VendorResponse(**v.model_dump()) for v in vendors]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    request: VendorCreateRequest,
    user: CurrentUser = Depends(require_permission("vendors:write")),
    svc=Depends(get_vendor_service),
):
    vendor = await svc.create_vendor(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=VendorResponse(**vendor.model_dump()), message=f"Vendor '{vendor.vendor_id}' created")


@router.get("/{vendor_id}", response_model=APIResponse)
async def get_vendor(vendor_id: str, user: CurrentUser, svc=Depends(get_vendor_service)):
    vendor = await svc.get_vendor(vendor_id)
    if not vendor: raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found")
    return APIResponse(data=VendorResponse(**vendor.model_dump()))


@router.patch("/{vendor_id}", response_model=APIResponse)
async def update_vendor(
    vendor_id: str, request: VendorUpdateRequest,
    user: CurrentUser = Depends(require_permission("vendors:write")),
    svc=Depends(get_vendor_service),
):
    updated = await svc.update_vendor(vendor_id, request.model_dump(exclude_unset=True), updated_by=user.user_id)
    if not updated: raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found")
    return APIResponse(data=VendorResponse(**updated.model_dump()))


@router.get("/{vendor_id}/performance", response_model=APIResponse)
async def get_vendor_performance(vendor_id: str, user: CurrentUser, svc=Depends(get_vendor_service)):
    perf = await svc.get_vendor_performance(vendor_id)
    return APIResponse(data=perf)


# ── Contracts ──────────────────────────────────────────────────

@router.get("/{vendor_id}/contracts")
async def list_vendor_contracts(vendor_id: str, user: CurrentUser, svc=Depends(get_vendor_service)):
    contracts, total = await svc.get_vendor_contracts(vendor_id)
    return APIResponse(data=[ContractResponse(**c.model_dump()) for c in contracts])


@router.post("/{vendor_id}/contracts", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    vendor_id: str, request: ContractCreateRequest,
    user: CurrentUser = Depends(require_permission("vendors:write")),
    svc=Depends(get_vendor_service),
):
    data = request.model_dump()
    data["vendor_id"] = vendor_id
    contract = await svc.create_contract(data, created_by=user.user_id)
    return APIResponse(data=ContractResponse(**contract.model_dump()))


# ── SLAs ───────────────────────────────────────────────────────

@router.post("/contracts/{contract_id}/slas", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_sla(
    contract_id: str, request: SLACreateRequest,
    user: CurrentUser = Depends(require_permission("vendors:write")),
    svc=Depends(get_vendor_service),
):
    data = request.model_dump()
    data["contract_id"] = contract_id
    sla = await svc.create_sla(data)
    return APIResponse(data=SLAResponse(**sla.model_dump()))


@router.get("/contracts/{contract_id}/slas", response_model=APIResponse)
async def list_contract_slas(contract_id: str, user: CurrentUser, svc=Depends(get_vendor_service)):
    slas, _ = await svc.get_contract_slas(contract_id)
    return APIResponse(data=[SLAResponse(**s.model_dump()) for s in slas])
