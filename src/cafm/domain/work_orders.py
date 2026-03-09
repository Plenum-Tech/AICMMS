"""Work order domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.domain.enums import WorkOrderPriority, WorkOrderStatus, WorkOrderType
from cafm.models.base import CAFMBaseModel


class WorkOrder(CAFMBaseModel):
    """A maintenance or service work order."""

    work_order_id: str
    title: str
    description: str | None = None
    work_order_type: WorkOrderType = WorkOrderType.CORRECTIVE
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM

    # Location
    building_id: str | None = None
    floor_id: str | None = None
    space_id: str | None = None
    asset_id: str | None = None

    # People
    requested_by: str | None = None
    assigned_to: str | None = None
    vendor_id: str | None = None

    # Dates
    requested_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    due_date: datetime | None = None

    # Cost
    estimated_cost: float | None = None
    actual_cost: float | None = None
    labor_hours: float | None = None

    # AI-relevant
    resolution_notes: str | None = None
    root_cause: str | None = None
    failure_code: str | None = None
    customer_satisfaction: float | None = None  # 1-5 scale

    # Extensibility
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class WorkOrderTask(CAFMBaseModel):
    """A sub-task within a work order."""

    task_id: str
    work_order_id: str
    sequence: int
    description: str
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    assigned_to: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    completed_at: datetime | None = None
    notes: str | None = None
