"""Request/response schemas for the technicians / manpower API."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field


class TechnicianCreateRequest(BaseModel):
    """Request to create a technician record."""

    technician_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    employee_id: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    vendor_id: str | None = None
    home_base_building_id: str | None = None
    skill_codes: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    shift_start: time | None = None
    shift_end: time | None = None
    days_off: list[str] = Field(default_factory=list)


class TechnicianUpdateRequest(BaseModel):
    """Request to update a technician."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    vendor_id: str | None = None
    skill_codes: list[str] | None = None
    certifications: list[str] | None = None
    is_available: bool | None = None
    shift_start: time | None = None
    shift_end: time | None = None


class TechnicianResponse(BaseModel):
    """Technician data returned by the API."""

    technician_id: str
    first_name: str
    last_name: str
    employee_id: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None
    vendor_id: str | None = None
    home_base_building_id: str | None = None
    skill_codes: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    is_available: bool = True
    avg_response_time_hours: float | None = None
    avg_resolution_time_hours: float | None = None
    total_work_orders_completed: int = 0
    customer_satisfaction_avg: float | None = None
    current_workload_count: int = 0
    gamification_points: int = 0
    gamification_level: int = 1
    impact_points: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TechnicianRoutingResponse(BaseModel):
    """AI-recommended technician for a work order."""

    technician_id: str
    technician_name: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    estimated_response_hours: float | None = None
    current_workload: int = 0
    skill_match: bool = True
