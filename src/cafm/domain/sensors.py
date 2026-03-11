"""IoT sensor and device domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.domain.enums import DeviceStatus, SensorType
from cafm.models.base import CAFMBaseModel


class IoTDevice(CAFMBaseModel):
    """An IoT sensor or device installed in the facility."""

    device_id: str
    name: str
    device_type: SensorType
    asset_id: str | None = None
    space_id: str | None = None
    building_id: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    firmware_version: str | None = None
    status: DeviceStatus = DeviceStatus.ONLINE
    installed_at: datetime | None = None
    last_seen: datetime | None = None
    measurement_unit: str | None = None  # e.g., "celsius", "percent", "kWh"
    min_threshold: float | None = None
    max_threshold: float | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class SensorReading(CAFMBaseModel):
    """A single reading from an IoT sensor."""

    reading_id: str
    device_id: str
    timestamp: datetime
    value: float
    unit: str | None = None
    quality: str | None = None  # "good", "suspect", "bad"
    is_anomaly: bool = False


class Threshold(CAFMBaseModel):
    """Alert threshold configuration for a sensor."""

    threshold_id: str
    device_id: str
    metric: str
    min_value: float | None = None
    max_value: float | None = None
    alert_severity: str = "warning"  # info, warning, critical
    notification_channels: list[str] = Field(default_factory=list)
    is_active: bool = True
    description: str | None = None
