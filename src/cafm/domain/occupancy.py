"""Occupancy and space utilization domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class OccupancyData(CAFMBaseModel):
    """Point-in-time occupancy reading for a space."""

    reading_id: str
    space_id: str
    building_id: str
    timestamp: datetime
    occupant_count: int
    capacity: int | None = None
    utilization_pct: float | None = None  # occupant_count / capacity * 100
    source: str | None = None  # e.g., "sensor", "badge", "manual"


class SpaceUtilization(CAFMBaseModel):
    """Aggregated utilization metrics for a space over a time period."""

    space_id: str
    building_id: str
    period_start: datetime
    period_end: datetime
    avg_occupancy: float | None = None
    peak_occupancy: int | None = None
    avg_utilization_pct: float | None = None
    peak_utilization_pct: float | None = None
    total_hours_occupied: float | None = None
    total_hours_available: float | None = None


class Reservation(CAFMBaseModel):
    """Space reservation / booking."""

    reservation_id: str
    space_id: str
    building_id: str
    title: str | None = None
    reserved_by: str
    start_time: datetime
    end_time: datetime
    attendee_count: int | None = None
    status: str = "confirmed"  # confirmed, cancelled, checked_in, no_show
    notes: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class MoveRequest(CAFMBaseModel):
    """Request to relocate personnel or equipment."""

    move_id: str
    requested_by: str
    move_type: str  # "personnel", "equipment", "department"
    from_space_id: str | None = None
    to_space_id: str | None = None
    scheduled_date: datetime | None = None
    status: str = "requested"  # requested, approved, in_progress, completed, cancelled
    description: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
