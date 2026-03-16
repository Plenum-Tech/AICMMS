"""Costs, invoices, budgets, and commercial tracking API routes (Story 12)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.costs import (
    BudgetResponse, CostCenterResponse,
    ExpenseCreateRequest, ExpenseResponse,
    InvoiceCreateRequest, InvoiceResponse, InvoiceUpdateRequest,
)

router = APIRouter(prefix="/costs", tags=["Costs & Finance"])

_cost_service = None


def get_cost_service():
    if _cost_service is None:
        raise HTTPException(status_code=503, detail="Cost service not initialized")
    return _cost_service


def set_cost_service(svc) -> None:
    global _cost_service
    _cost_service = svc


# ── Expenses ──────────────────────────────────────────────────


@router.get("/expenses", response_model=PaginatedResponse[ExpenseResponse])
async def list_expenses(
    pagination: Pagination, user: CurrentUser,
    work_order_id: str | None = Query(None), vendor_id: str | None = Query(None),
    category: str | None = Query(None),
    svc=Depends(get_cost_service),
):
    filters = {}
    if work_order_id: filters["work_order_id"] = work_order_id
    if vendor_id: filters["vendor_id"] = vendor_id
    if category: filters["category"] = category
    expenses, total = await svc.list_expenses(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [ExpenseResponse(**e.model_dump()) for e in expenses]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/expenses", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    request: ExpenseCreateRequest,
    user: CurrentUser = Depends(require_permission("costs:write")),
    svc=Depends(get_cost_service),
):
    expense = await svc.create_expense(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=ExpenseResponse(**expense.model_dump()), message="Expense recorded")


# ── Invoices ──────────────────────────────────────────────────


@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    pagination: Pagination, user: CurrentUser,
    vendor_id: str | None = Query(None), invoice_status: str | None = Query(None, alias="status"),
    svc=Depends(get_cost_service),
):
    filters = {}
    if vendor_id: filters["vendor_id"] = vendor_id
    if invoice_status: filters["status"] = invoice_status
    invoices, total = await svc.list_invoices(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [InvoiceResponse(**i.model_dump()) for i in invoices]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/invoices", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: InvoiceCreateRequest,
    user: CurrentUser = Depends(require_permission("costs:write")),
    svc=Depends(get_cost_service),
):
    invoice = await svc.create_invoice(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=InvoiceResponse(**invoice.model_dump()), message=f"Invoice '{invoice.invoice_id}' created")


@router.get("/invoices/{invoice_id}", response_model=APIResponse)
async def get_invoice(invoice_id: str, user: CurrentUser, svc=Depends(get_cost_service)):
    invoice = await svc.get_invoice(invoice_id)
    if not invoice: raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found")
    return APIResponse(data=InvoiceResponse(**invoice.model_dump()))


@router.patch("/invoices/{invoice_id}", response_model=APIResponse)
async def update_invoice(
    invoice_id: str, request: InvoiceUpdateRequest,
    user: CurrentUser = Depends(require_permission("costs:write")),
    svc=Depends(get_cost_service),
):
    updated = await svc.update_invoice(invoice_id, request.model_dump(exclude_unset=True))
    if not updated: raise HTTPException(status_code=404, detail=f"Invoice '{invoice_id}' not found")
    return APIResponse(data=InvoiceResponse(**updated.model_dump()))


# ── Budgets ───────────────────────────────────────────────────


@router.get("/budgets", response_model=PaginatedResponse[BudgetResponse])
async def list_budgets(
    pagination: Pagination, user: CurrentUser,
    cost_center_id: str | None = Query(None), fiscal_year: int | None = Query(None),
    svc=Depends(get_cost_service),
):
    filters = {}
    if cost_center_id: filters["cost_center_id"] = cost_center_id
    if fiscal_year: filters["fiscal_year"] = fiscal_year
    budgets, total = await svc.list_budgets(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [BudgetResponse(**b.model_dump()) for b in budgets]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


# ── Cost Centers ──────────────────────────────────────────────


@router.get("/cost-centers", response_model=APIResponse)
async def list_cost_centers(
    user: CurrentUser,
    department: str | None = Query(None),
    svc=Depends(get_cost_service),
):
    filters = {}
    if department: filters["department"] = department
    centers, total = await svc.list_cost_centers(filters=filters or None)
    items = [CostCenterResponse(**c.model_dump()) for c in centers]
    return APIResponse(data={"cost_centers": items, "total": total})


# ── WO → Commercial Journey (Story 12) ───────────────────────


@router.get("/wo-journey/{work_order_id}", response_model=APIResponse)
async def get_wo_commercial_journey(
    work_order_id: str,
    user: CurrentUser = Depends(require_permission("costs:read")),
    svc=Depends(get_cost_service),
):
    """Track the full commercial journey of a work order (Story 12).

    WO → Expenses → Invoices → PO, with breakage detection.
    """
    journey = await svc.get_wo_commercial_journey(work_order_id)
    return APIResponse(data=journey, message="Commercial journey retrieved")


# ── Cost Summary ──────────────────────────────────────────────


@router.get("/summary", response_model=APIResponse)
async def get_cost_summary(
    user: CurrentUser = Depends(require_permission("costs:read")),
    svc=Depends(get_cost_service),
):
    """Get overall cost management summary for dashboard."""
    summary = await svc.get_cost_summary()
    return APIResponse(data=summary)
