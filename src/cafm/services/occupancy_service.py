"""Service layer for occupancy data and space utilization."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.occupancy import OccupancyData, Reservation, SpaceUtilization
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class OccupancyService:
    """Business logic for occupancy tracking, utilization analytics, and reservations."""

    def __init__(
        self,
        occupancy_repo: Repository[OccupancyData],
        utilization_repo: Repository[SpaceUtilization],
        reservation_repo: Repository[Reservation],
        event_bus: EventBus,
    ) -> None:
        self._occupancy_repo = occupancy_repo
        self._utilization_repo = utilization_repo
        self._reservation_repo = reservation_repo
        self._event_bus = event_bus

    # ── Occupancy ─────────────────────────────────────────────

    async def get_current_occupancy(
        self,
        building_id: str | None = None,
        space_id: str | None = None,
    ) -> list[OccupancyData]:
        """Get current occupancy data, optionally filtered."""
        filters: dict[str, Any] = {}
        if building_id: filters["building_id"] = building_id
        if space_id: filters["space_id"] = space_id
        result = await self._occupancy_repo.get_all(
            filters=filters or None, limit=500,
        )
        return [OccupancyData(**r.data) for r in result.records]

    # ── Utilization ───────────────────────────────────────────

    async def get_utilization(
        self,
        building_id: str | None = None,
        space_id: str | None = None,
        period: str = "weekly",
    ) -> list[SpaceUtilization]:
        """Get space utilization metrics."""
        filters: dict[str, Any] = {}
        if building_id: filters["building_id"] = building_id
        if space_id: filters["space_id"] = space_id
        if period: filters["period"] = period
        result = await self._utilization_repo.get_all(
            filters=filters or None, limit=500,
        )
        return [SpaceUtilization(**r.data) for r in result.records]

    async def get_heatmap(
        self,
        building_id: str,
        floor_id: str | None = None,
    ) -> dict[str, Any]:
        """Get occupancy heatmap data for visualization.

        Returns space-level occupancy with coordinates for rendering.
        """
        occupancy_data = await self.get_current_occupancy(building_id=building_id)
        spaces = []
        for occ in occupancy_data:
            spaces.append({
                "space_id": occ.space_id,
                "occupant_count": occ.occupant_count,
                "capacity": occ.capacity,
                "utilization_pct": occ.utilization_pct,
            })
        return {
            "building_id": building_id,
            "floor_id": floor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "spaces": spaces,
            "total_spaces": len(spaces),
        }

    # ── Reservations ──────────────────────────────────────────

    async def list_reservations(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Reservation], int]:
        result = await self._reservation_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._reservation_repo.count(filters=filters)
        reservations = [Reservation(**r.data) for r in result.records]
        return reservations, total

    async def create_reservation(
        self, data: dict[str, Any], created_by: str | None = None,
    ) -> Reservation:
        data["created_at"] = datetime.utcnow()
        data["status"] = "confirmed"
        reservation = Reservation(**data)
        created = await self._reservation_repo.create(reservation)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="occupancy_service",
            payload={"entity": "reservation", "reservation_id": created.reservation_id},
        ))
        return created

    async def get_reservation(self, reservation_id: str) -> Reservation | None:
        return await self._reservation_repo.get_by_id(reservation_id)

    async def cancel_reservation(
        self, reservation_id: str, cancelled_by: str | None = None,
    ) -> Reservation | None:
        return await self._reservation_repo.update(reservation_id, {
            "status": "cancelled",
            "updated_at": datetime.utcnow(),
        })
