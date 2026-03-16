"""Request/response schemas for the sensors/IoT API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import DeviceStatus, SensorType


class DeviceCreateRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    device_type: SensorType
    asset_id: str | None = None
    space_id: str | None = None
    building_id: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    measurement_unit: str | None = None
    min_threshold: float | None = None
    max_threshold: float | None = None


class DeviceResponse(BaseModel):
    device_id: str
    name: str
    device_type: SensorType
    asset_id: str | None = None
    space_id: str | None = None
    building_id: str | None = None
    status: DeviceStatus
    measurement_unit: str | None = None
    min_threshold: float | None = None
    max_threshold: float | None = None
    last_seen: datetime | None = None
    created_at: datetime | None = None


class SensorReadingInput(BaseModel):
    device_id: str
    value: float
    unit: str | None = None
    quality: str | None = "good"


class SensorReadingResponse(BaseModel):
    reading_id: str
    device_id: str
    timestamp: datetime
    value: float
    unit: str | None = None
    quality: str | None = None
    is_anomaly: bool = False


class ThresholdResponse(BaseModel):
    threshold_id: str
    device_id: str
    metric: str
    min_value: float | None = None
    max_value: float | None = None
    alert_severity: str
    is_active: bool = True
