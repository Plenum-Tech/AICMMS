"""Request/response schemas for the costs & financial API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class ExpenseCreateRequest(BaseModel):
    expense_id: str = Field(..., min_length=1, max_length=50)
    cost_center_id: str
    budget_id: str | None = None
    work_order_id: str | None = None
    vendor_id: str | None = None
    asset_id: str | None = None
    category: str
    amount: float
    currency: str = "USD"
    expense_date: date
    description: str | None = None
    invoice_number: str | None = None


class ExpenseResponse(BaseModel):
    expense_id: str
    cost_center_id: str
    budget_id: str | None = None
    work_order_id: str | None = None
    vendor_id: str | None = None
    asset_id: str | None = None
    category: str
    amount: float
    currency: str
    expense_date: date
    description: str | None = None
    invoice_number: str | None = None
    approved_by: str | None = None
    created_at: datetime | None = None


class InvoiceCreateRequest(BaseModel):
    invoice_id: str = Field(..., min_length=1, max_length=50)
    vendor_id: str
    contract_id: str | None = None
    invoice_number: str
    amount: float
    currency: str = "USD"
    issue_date: date
    due_date: date | None = None
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None


class InvoiceUpdateRequest(BaseModel):
    status: str | None = None
    paid_date: date | None = None
    notes: str | None = None


class InvoiceResponse(BaseModel):
    invoice_id: str
    vendor_id: str
    contract_id: str | None = None
    invoice_number: str
    amount: float
    currency: str
    issue_date: date
    due_date: date | None = None
    paid_date: date | None = None
    status: str
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None


class BudgetResponse(BaseModel):
    budget_id: str
    cost_center_id: str
    fiscal_year: int
    period: str | None = None
    category: str | None = None
    allocated_amount: float
    spent_amount: float
    committed_amount: float
    remaining: float
    utilization_pct: float


class CostCenterResponse(BaseModel):
    cost_center_id: str
    name: str
    code: str
    department: str | None = None
    building_id: str | None = None
    is_active: bool = True


class WOCommercialJourney(BaseModel):
    """Track work order → invoice/PO journey (Story 12)."""
    work_order_id: str
    work_order_title: str
    work_order_status: str
    expenses: list[ExpenseResponse] = Field(default_factory=list)
    invoices: list[InvoiceResponse] = Field(default_factory=list)
    total_expense_amount: float = 0.0
    total_invoice_amount: float = 0.0
    has_breakage: bool = False
    breakage_details: list[str] = Field(default_factory=list)
