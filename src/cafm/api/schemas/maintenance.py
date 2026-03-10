"""Request/response schemas for the maintenance API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import MaintenanceFrequency


class MaintenanceScheduleCreateRequest(BaseModel):
    """Request to create a preventive maintenance schedule."""

    schedule_id: str = Field(..., min_length=1, max_length=50)
    asset_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    frequency: MaintenanceFrequency = MaintenanceFrequency.MONTHLY
    next_due_date: datetime | None = None
    estimated_duration_hours: float | None = None
    checklist_items: list[str] = Field(default_factory=list)
    assigned_to: str | None = None
    auto_generate_work_orders: bool = True


class MaintenanceScheduleResponse(BaseModel):
    """Maintenance schedule returned by the API."""

    schedule_id: str
    asset_id: str
    name: str
    description: str | None = None
    frequency: MaintenanceFrequency
    is_active: bool = True
    next_due_date: datetime | None = None
    last_completed: datetime | None = None
    estimated_duration_hours: float | None = None
    checklist_items: list[str] = Field(default_factory=list)
    assigned_to: str | None = None
    auto_generate_work_orders: bool = True
    created_at: datetime | None = None


class PPMInsightResponse(BaseModel):
    """Predictive/preventive maintenance insight from AI engine."""

    asset_id: str
    asset_name: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    predicted_failure_date: datetime | None = None
    recommended_action: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    factors: list[str] = Field(default_factory=list)
    suggested_schedule: MaintenanceFrequency | None = None
