"""Request/response schemas for the facilities API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import BuildingStatus, SpaceType


class BuildingCreateRequest(BaseModel):
    """Request to create a building."""

    building_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    address: str | None = None
    city: str | None = None
    country: str | None = None
    status: BuildingStatus = BuildingStatus.OPERATIONAL
    total_area_sqm: float | None = None
    floors_count: int | None = None
    year_built: int | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class BuildingResponse(BaseModel):
    """Building data returned by the API."""

    building_id: str
    name: str
    address: str | None = None
    city: str | None = None
    country: str | None = None
    status: BuildingStatus
    total_area_sqm: float | None = None
    floors_count: int | None = None
    year_built: int | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    asset_count: int | None = None
    active_work_orders: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SpaceResponse(BaseModel):
    """Space data returned by the API."""

    space_id: str
    name: str
    floor_id: str
    space_type: SpaceType
    area_sqm: float | None = None
    capacity: int | None = None
    is_bookable: bool = False
    current_occupancy: int | None = None
    utilization_pct: float | None = None
    created_at: datetime | None = None
