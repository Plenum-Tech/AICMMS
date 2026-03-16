"""Maintenance domain models: schedules, logs, failure modes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.domain.enums import FailureSeverity, MaintenanceFrequency
from cafm.models.base import CAFMBaseModel


class MaintenanceSchedule(CAFMBaseModel):
    """Preventive maintenance schedule template."""

    schedule_id: str
    name: str
    asset_id: str | None = None
    asset_category: str | None = None  # Apply to all assets in category
    frequency: MaintenanceFrequency = MaintenanceFrequency.MONTHLY
    custom_interval_days: int | None = None  # When frequency is CUSTOM
    description: str | None = None
    instructions: str | None = None
    estimated_duration_hours: float | None = None
    estimated_cost: float | None = None
    assigned_vendor_id: str | None = None
    is_active: bool = True
    last_executed: datetime | None = None
    next_due: datetime | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class MaintenanceLog(CAFMBaseModel):
    """Record of a completed maintenance activity."""

    log_id: str
    schedule_id: str | None = None
    work_order_id: str | None = None
    asset_id: str
    maintenance_type: str  # "preventive", "corrective", "predictive"
    performed_at: datetime
    performed_by: str | None = None
    vendor_id: str | None = None
    duration_hours: float | None = None
    cost: float | None = None
    findings: str | None = None
    actions_taken: str | None = None
    parts_used: list[str] = Field(default_factory=list)
    condition_before: str | None = None
    condition_after: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class FailureMode(CAFMBaseModel):
    """Known failure mode for an asset category."""

    failure_mode_id: str
    asset_category: str
    code: str
    name: str
    description: str | None = None
    severity: FailureSeverity = FailureSeverity.MODERATE
    typical_cause: str | None = None
    recommended_action: str | None = None
    mean_time_to_repair_hours: float | None = None
