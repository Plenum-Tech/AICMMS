"""Facility domain models: Building, Floor, Space, Zone."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from cafm.domain.enums import BuildingStatus, SpaceType
from cafm.models.base import CAFMBaseModel


class Building(CAFMBaseModel):
    """A physical building or structure."""

    building_id: str
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: BuildingStatus = BuildingStatus.OPERATIONAL
    total_area_sqft: float | None = None
    floor_count: int | None = None
    year_built: int | None = None
    building_type: str | None = None
    owner: str | None = None
    manager: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Floor(CAFMBaseModel):
    """A floor / level within a building."""

    floor_id: str
    building_id: str
    name: str
    level_number: int
    area_sqft: float | None = None
    description: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Space(CAFMBaseModel):
    """A space / room within a floor."""

    space_id: str
    floor_id: str
    building_id: str
    name: str
    space_type: SpaceType = SpaceType.OTHER
    area_sqft: float | None = None
    capacity: int | None = None
    is_bookable: bool = False
    department: str | None = None
    cost_center: str | None = None
    description: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Zone(CAFMBaseModel):
    """A logical zone grouping multiple spaces (e.g., fire zone, HVAC zone)."""

    zone_id: str
    building_id: str
    name: str
    zone_type: str
    space_ids: list[str] = Field(default_factory=list)
    description: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
