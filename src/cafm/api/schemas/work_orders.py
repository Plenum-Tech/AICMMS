"""Request/response schemas for the work orders API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import WorkOrderPriority, WorkOrderStatus, WorkOrderType


class WorkOrderCreateRequest(BaseModel):
    """Request to create a new work order."""

    work_order_id: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    work_order_type: WorkOrderType = WorkOrderType.CORRECTIVE
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    building_id: str | None = None
    floor_id: str | None = None
    space_id: str | None = None
    asset_id: str | None = None
    requested_by: str | None = None
    assigned_to: str | None = None
    vendor_id: str | None = None
    due_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    estimated_cost: float | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class WorkOrderUpdateRequest(BaseModel):
    """Request to update a work order."""

    title: str | None = None
    description: str | None = None
    status: WorkOrderStatus | None = None
    priority: WorkOrderPriority | None = None
    assigned_to: str | None = None
    vendor_id: str | None = None
    due_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    labor_hours: float | None = None
    resolution_notes: str | None = None
    root_cause: str | None = None
    failure_code: str | None = None
    custom_attributes: dict[str, Any] | None = None
    tags: list[str] | None = None


class WorkOrderResponse(BaseModel):
    """Work order returned by the API."""

    work_order_id: str
    title: str
    description: str | None = None
    work_order_type: WorkOrderType
    status: WorkOrderStatus
    priority: WorkOrderPriority
    building_id: str | None = None
    floor_id: str | None = None
    space_id: str | None = None
    asset_id: str | None = None
    requested_by: str | None = None
    assigned_to: str | None = None
    vendor_id: str | None = None
    requested_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    due_date: datetime | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    labor_hours: float | None = None
    resolution_notes: str | None = None
    root_cause: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkOrderAdHocRequest(BaseModel):
    """Create an ad-hoc work order from text/voice (per AICMMS spec)."""

    text: str = Field(..., min_length=1, description="Description text or transcribed voice note")
    building_id: str | None = None
    asset_id: str | None = None
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    requested_by: str | None = None


class WorkOrderFilterParams(BaseModel):
    """Filtering parameters for work order queries."""

    status: WorkOrderStatus | None = None
    priority: WorkOrderPriority | None = None
    work_order_type: WorkOrderType | None = None
    building_id: str | None = None
    asset_id: str | None = None
    assigned_to: str | None = None
    vendor_id: str | None = None
    search: str | None = None
