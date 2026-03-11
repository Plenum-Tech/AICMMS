"""Financial domain models: cost centers, budgets, expenses."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class CostCenter(CAFMBaseModel):
    """Organizational unit for cost allocation."""

    cost_center_id: str
    name: str
    code: str
    parent_id: str | None = None
    department: str | None = None
    building_id: str | None = None
    description: str | None = None
    is_active: bool = True


class Budget(CAFMBaseModel):
    """Budget allocation for a cost center and fiscal period."""

    budget_id: str
    cost_center_id: str
    fiscal_year: int
    period: str | None = None  # e.g., "Q1", "January", "Annual"
    category: str | None = None  # e.g., "maintenance", "utilities", "capital"
    allocated_amount: float
    spent_amount: float = 0.0
    committed_amount: float = 0.0  # Approved but not yet spent
    description: str | None = None

    @property
    def remaining(self) -> float:
        return self.allocated_amount - self.spent_amount - self.committed_amount

    @property
    def utilization_pct(self) -> float:
        if self.allocated_amount == 0:
            return 0.0
        return (self.spent_amount / self.allocated_amount) * 100


class Expense(CAFMBaseModel):
    """An individual expense record."""

    expense_id: str
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
    approved_by: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Invoice(CAFMBaseModel):
    """Vendor invoice."""

    invoice_id: str
    vendor_id: str
    contract_id: str | None = None
    invoice_number: str
    amount: float
    currency: str = "USD"
    issue_date: date
    due_date: date | None = None
    paid_date: date | None = None
    status: str = "pending"  # pending, approved, paid, disputed
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None
