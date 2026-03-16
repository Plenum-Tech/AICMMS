"""Service layer for costs, invoices, and commercial tracking (Story 12)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.costs import Budget, CostCenter, Expense, Invoice
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class CostService:
    """Business logic for financial management and inspection-to-commercial tracking.

    Story 12: Track work order → invoice/PO journey, notify on breakages.
    """

    def __init__(
        self,
        expense_repo: Repository[Expense],
        invoice_repo: Repository[Invoice],
        budget_repo: Repository[Budget],
        cost_center_repo: Repository[CostCenter],
        event_bus: EventBus,
    ) -> None:
        self._expense_repo = expense_repo
        self._invoice_repo = invoice_repo
        self._budget_repo = budget_repo
        self._cost_center_repo = cost_center_repo
        self._event_bus = event_bus

    # ── Expenses ───────────────────────────────────────────────

    async def create_expense(self, data: dict[str, Any], created_by: str | None = None) -> Expense:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        expense = Expense(**data)
        return await self._expense_repo.create(expense)

    async def list_expenses(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Expense], int]:
        result = await self._expense_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._expense_repo.count(filters=filters)
        expenses = [Expense(**r.data) for r in result.records]
        return expenses, total

    # ── Invoices ───────────────────────────────────────────────

    async def create_invoice(self, data: dict[str, Any], created_by: str | None = None) -> Invoice:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        invoice = Invoice(**data)
        created = await self._invoice_repo.create(invoice)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="cost_service",
            payload={"entity": "invoice", "invoice_id": created.invoice_id},
        ))
        return created

    async def get_invoice(self, invoice_id: str) -> Invoice | None:
        return await self._invoice_repo.get_by_id(invoice_id)

    async def list_invoices(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        result = await self._invoice_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._invoice_repo.count(filters=filters)
        invoices = [Invoice(**r.data) for r in result.records]
        return invoices, total

    async def update_invoice(
        self, invoice_id: str, updates: dict[str, Any],
    ) -> Invoice | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._invoice_repo.update(invoice_id, updates)

    # ── Budgets ────────────────────────────────────────────────

    async def list_budgets(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Budget], int]:
        result = await self._budget_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._budget_repo.count(filters=filters)
        budgets = [Budget(**r.data) for r in result.records]
        return budgets, total

    # ── Cost Centers ───────────────────────────────────────────

    async def list_cost_centers(
        self, filters: dict[str, Any] | None = None,
    ) -> tuple[list[CostCenter], int]:
        result = await self._cost_center_repo.get_all(filters=filters)
        total = await self._cost_center_repo.count(filters=filters)
        centers = [CostCenter(**r.data) for r in result.records]
        return centers, total

    # ── WO → Commercial Journey (Story 12) ─────────────────────

    async def get_wo_commercial_journey(self, work_order_id: str) -> dict[str, Any]:
        """Track the full commercial journey of a work order.

        Checks: WO → Expenses → Invoices → PO and detects breakages.
        """
        expenses, exp_count = await self.list_expenses(
            filters={"work_order_id": work_order_id},
        )
        invoices = []
        # Get invoices linked via vendor from expenses
        vendor_ids = {e.vendor_id for e in expenses if e.vendor_id}
        for vid in vendor_ids:
            vendor_invoices, _ = await self.list_invoices(filters={"vendor_id": vid})
            invoices.extend(vendor_invoices)

        total_expense = sum(e.amount for e in expenses)
        total_invoice = sum(i.amount for i in invoices)

        # Detect breakages
        breakages: list[str] = []
        if expenses and not invoices:
            breakages.append("Expenses recorded but no invoice generated")
        pending_invoices = [i for i in invoices if i.status == "pending"]
        if pending_invoices:
            breakages.append(f"{len(pending_invoices)} invoice(s) pending approval")
        overdue_invoices = [
            i for i in invoices
            if i.due_date and i.status != "paid" and i.due_date < datetime.utcnow().date()
        ]
        if overdue_invoices:
            breakages.append(f"{len(overdue_invoices)} overdue invoice(s)")

        return {
            "work_order_id": work_order_id,
            "expenses": [e.model_dump() for e in expenses],
            "invoices": [i.model_dump() for i in invoices],
            "total_expense_amount": total_expense,
            "total_invoice_amount": total_invoice,
            "has_breakage": len(breakages) > 0,
            "breakage_details": breakages,
        }

    async def get_cost_summary(self) -> dict[str, Any]:
        """Get overall cost management summary for dashboard."""
        expenses, total_expenses = await self.list_expenses(limit=1000)
        invoices, total_invoices = await self.list_invoices(limit=1000)
        total_spent = sum(e.amount for e in expenses)
        total_invoiced = sum(i.amount for i in invoices)
        pending_invoices = [i for i in invoices if i.status == "pending"]

        return {
            "total_expenses": total_expenses,
            "total_invoices": total_invoices,
            "total_spent": total_spent,
            "total_invoiced": total_invoiced,
            "pending_invoices_count": len(pending_invoices),
            "pending_invoices_amount": sum(i.amount for i in pending_invoices),
        }
