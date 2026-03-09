"""Manpower / technician domain models.

Covers the manpower registry, skills tracking, availability and
technician performance metrics required by AICMMS spec.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class Technician(CAFMBaseModel):
    """A field technician or FM team member."""

    technician_id: str
    first_name: str
    last_name: str
    employee_id: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None  # e.g., "senior_technician", "supervisor", "helper"
    vendor_id: str | None = None  # If subcontracted

    # Location
    current_location: str | None = None
    home_base_building_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Skills
    skill_codes: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    experience_years: float | None = None

    # Availability
    is_available: bool = True
    shift_start: time | None = None
    shift_end: time | None = None
    days_off: list[str] = Field(default_factory=list)  # e.g., ["friday", "saturday"]

    # Performance — AI-relevant
    avg_response_time_hours: float | None = None
    avg_resolution_time_hours: float | None = None
    total_work_orders_completed: int = 0
    customer_satisfaction_avg: float | None = None  # 1-5
    current_workload_count: int = 0

    # Gamification
    gamification_points: int = 0
    gamification_level: int = 1
    impact_points: int = 0

    # Profile
    profile_photo_url: str | None = None
    notes: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class TechnicianSkill(CAFMBaseModel):
    """Detailed skill record for a technician."""

    skill_id: str
    technician_id: str
    skill_code: str
    skill_name: str
    proficiency_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    certified: bool = False
    certification_date: date | None = None
    certification_expiry: date | None = None
    notes: str | None = None


class TechnicianAvailability(CAFMBaseModel):
    """Availability slot for scheduling and routing."""

    availability_id: str
    technician_id: str
    date: date
    start_time: time
    end_time: time
    is_available: bool = True
    reason: str | None = None  # e.g., "leave", "training", "other_site"
