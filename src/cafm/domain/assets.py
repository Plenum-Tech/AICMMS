"""Asset domain models: Asset, AssetCategory, AssetLifecycle."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from cafm.domain.enums import AssetCondition, AssetCriticality, AssetStatus
from cafm.models.base import CAFMBaseModel


class AssetCategory(CAFMBaseModel):
    """Asset classification category."""

    code: str
    name: str
    parent_code: str | None = None
    useful_life_years: int | None = None
    description: str | None = None


class Asset(CAFMBaseModel):
    """Core asset entity for facility management."""

    asset_id: str
    name: str
    category: str  # FK to AssetCategory.code
    facility_id: str  # FK to Building.building_id
    floor_id: str | None = None
    space_id: str | None = None

    # Identification
    serial_number: str | None = None
    barcode: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None

    # Status
    status: AssetStatus = AssetStatus.ACTIVE
    condition: AssetCondition = AssetCondition.GOOD
    criticality: AssetCriticality = AssetCriticality.MEDIUM

    # Dates
    purchase_date: date | None = None
    installation_date: date | None = None
    warranty_expiry: date | None = None
    expected_end_of_life: date | None = None

    # Financial
    purchase_cost: float | None = None
    current_value: float | None = None
    replacement_cost: float | None = None
    salvage_value: float | None = None

    # AI-relevant fields
    last_maintenance: datetime | None = None
    failure_count: int = 0
    mean_time_between_failures: float | None = None  # hours
    total_downtime_hours: float | None = None

    # Extensibility
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class AssetLifecycleEvent(CAFMBaseModel):
    """Tracks significant events in an asset's lifecycle."""

    event_id: str
    asset_id: str
    event_type: str  # e.g., "installed", "repaired", "relocated", "decommissioned"
    event_date: datetime
    description: str | None = None
    performed_by: str | None = None
    cost: float | None = None
    notes: str | None = None
