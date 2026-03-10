"""Request/response schemas for the assets API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import AssetCondition, AssetCriticality, AssetStatus


class AssetCreateRequest(BaseModel):
    """Request to create a new asset."""

    asset_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    category: str
    facility_id: str
    floor_id: str | None = None
    space_id: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    onboarding_method: str | None = "manual"
    status: AssetStatus = AssetStatus.ACTIVE
    condition: AssetCondition = AssetCondition.GOOD
    criticality: AssetCriticality = AssetCriticality.MEDIUM
    purchase_date: date | None = None
    installation_date: date | None = None
    warranty_expiry: date | None = None
    purchase_cost: float | None = None
    replacement_cost: float | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class AssetUpdateRequest(BaseModel):
    """Request to update an asset."""

    name: str | None = None
    category: str | None = None
    status: AssetStatus | None = None
    condition: AssetCondition | None = None
    criticality: AssetCriticality | None = None
    floor_id: str | None = None
    space_id: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    warranty_expiry: date | None = None
    purchase_cost: float | None = None
    replacement_cost: float | None = None
    custom_attributes: dict[str, Any] | None = None
    tags: list[str] | None = None


class AssetResponse(BaseModel):
    """Asset data returned by the API."""

    asset_id: str
    name: str
    category: str
    facility_id: str
    floor_id: str | None = None
    space_id: str | None = None
    serial_number: str | None = None
    barcode: str | None = None
    qr_code: str | None = None
    qr_code_url: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    onboarding_method: str | None = None
    spec_document_urls: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    status: AssetStatus
    condition: AssetCondition
    criticality: AssetCriticality
    purchase_date: date | None = None
    installation_date: date | None = None
    warranty_expiry: date | None = None
    expected_end_of_life: date | None = None
    purchase_cost: float | None = None
    current_value: float | None = None
    replacement_cost: float | None = None
    last_maintenance: datetime | None = None
    failure_count: int = 0
    mean_time_between_failures: float | None = None
    total_downtime_hours: float | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssetFilterParams(BaseModel):
    """Filtering parameters for asset queries."""

    facility_id: str | None = None
    floor_id: str | None = None
    category: str | None = None
    status: AssetStatus | None = None
    condition: AssetCondition | None = None
    criticality: AssetCriticality | None = None
    search: str | None = None  # Full-text search on name/serial
