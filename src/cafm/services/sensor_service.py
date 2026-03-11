"""Service layer for IoT sensors and devices."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.sensors import IoTDevice, SensorReading, Threshold
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class SensorService:
    """Business logic for IoT device management and sensor data ingestion."""

    def __init__(
        self,
        device_repo: Repository[IoTDevice],
        reading_repo: Repository[SensorReading],
        threshold_repo: Repository[Threshold],
        event_bus: EventBus,
    ) -> None:
        self._device_repo = device_repo
        self._reading_repo = reading_repo
        self._threshold_repo = threshold_repo
        self._event_bus = event_bus

    # ── Devices ───────────────────────────────────────────────

    async def create_device(
        self, data: dict[str, Any], created_by: str | None = None,
    ) -> IoTDevice:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        device = IoTDevice(**data)
        return await self._device_repo.create(device)

    async def get_device(self, device_id: str) -> IoTDevice | None:
        return await self._device_repo.get_by_id(device_id)

    async def list_devices(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[IoTDevice], int]:
        result = await self._device_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._device_repo.count(filters=filters)
        devices = [IoTDevice(**r.data) for r in result.records]
        return devices, total

    # ── Readings ──────────────────────────────────────────────

    async def ingest_reading(self, data: dict[str, Any]) -> SensorReading:
        """Ingest a single sensor reading with threshold checking."""
        if "reading_id" not in data:
            data["reading_id"] = f"SR-{uuid.uuid4().hex[:8].upper()}"
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()

        reading = SensorReading(**data)

        # Check thresholds for anomaly detection
        reading.is_anomaly = await self._check_thresholds(reading)

        created = await self._reading_repo.create(reading)

        # Update device last_seen
        await self._device_repo.update(reading.device_id, {
            "last_seen": reading.timestamp,
        })

        if reading.is_anomaly:
            await self._event_bus.publish(Event(
                type=EventType.THRESHOLD_BREACHED, source="sensor_service",
                payload={
                    "device_id": reading.device_id,
                    "value": reading.value,
                    "reading_id": reading.reading_id,
                },
            ))

        return created

    async def ingest_readings_batch(
        self, readings_data: list[dict[str, Any]],
    ) -> list[SensorReading]:
        """Ingest multiple readings."""
        results = []
        for data in readings_data:
            reading = await self.ingest_reading(data)
            results.append(reading)
        return results

    async def get_device_readings(
        self, device_id: str, limit: int = 100,
    ) -> tuple[list[SensorReading], int]:
        result = await self._reading_repo.get_all(
            filters={"device_id": device_id}, limit=limit,
        )
        total = await self._reading_repo.count(filters={"device_id": device_id})
        readings = [SensorReading(**r.data) for r in result.records]
        return readings, total

    async def get_latest_reading(self, device_id: str) -> SensorReading | None:
        readings, _ = await self.get_device_readings(device_id, limit=1)
        return readings[0] if readings else None

    # ── Thresholds ────────────────────────────────────────────

    async def get_thresholds(self, device_id: str) -> list[Threshold]:
        result = await self._threshold_repo.get_all(
            filters={"device_id": device_id},
        )
        return [Threshold(**r.data) for r in result.records]

    async def _check_thresholds(self, reading: SensorReading) -> bool:
        """Check if reading breaches any threshold."""
        thresholds = await self.get_thresholds(reading.device_id)
        for t in thresholds:
            if not t.is_active:
                continue
            if t.min_value is not None and reading.value < t.min_value:
                return True
            if t.max_value is not None and reading.value > t.max_value:
                return True
        return False
