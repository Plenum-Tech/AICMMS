"""Service layer for facility management — buildings, floors, spaces."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.facilities import Building, Floor, Space
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class FacilityService:
    """Business logic for facility management."""

    def __init__(
        self,
        building_repo: Repository[Building],
        floor_repo: Repository[Floor],
        space_repo: Repository[Space],
        event_bus: EventBus,
    ) -> None:
        self._building_repo = building_repo
        self._floor_repo = floor_repo
        self._space_repo = space_repo
        self._event_bus = event_bus

    # ── Buildings ──────────────────────────────────────────────

    async def create_building(self, data: dict[str, Any], created_by: str | None = None) -> Building:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        building = Building(**data)
        created = await self._building_repo.create(building)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="facility_service",
            payload={"entity": "building", "building_id": created.building_id},
        ))
        return created

    async def get_building(self, building_id: str) -> Building | None:
        return await self._building_repo.get_by_id(building_id)

    async def list_buildings(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Building], int]:
        result = await self._building_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._building_repo.count(filters=filters)
        buildings = [Building(**r.data) for r in result.records]
        return buildings, total

    async def update_building(
        self, building_id: str, updates: dict[str, Any], updated_by: str | None = None,
    ) -> Building | None:
        updates["updated_at"] = datetime.utcnow()
        if updated_by:
            updates["updated_by"] = updated_by
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._building_repo.update(building_id, updates)

    async def delete_building(self, building_id: str) -> bool:
        return await self._building_repo.delete(building_id)

    # ── Floors ─────────────────────────────────────────────────

    async def create_floor(self, data: dict[str, Any]) -> Floor:
        data["created_at"] = datetime.utcnow()
        floor = Floor(**data)
        return await self._floor_repo.create(floor)

    async def list_floors(self, building_id: str) -> tuple[list[Floor], int]:
        result = await self._floor_repo.get_all(filters={"building_id": building_id})
        total = await self._floor_repo.count(filters={"building_id": building_id})
        floors = [Floor(**r.data) for r in result.records]
        return floors, total

    # ── Spaces ─────────────────────────────────────────────────

    async def create_space(self, data: dict[str, Any]) -> Space:
        data["created_at"] = datetime.utcnow()
        space = Space(**data)
        return await self._space_repo.create(space)

    async def get_space(self, space_id: str) -> Space | None:
        return await self._space_repo.get_by_id(space_id)

    async def list_spaces(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Space], int]:
        result = await self._space_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._space_repo.count(filters=filters)
        spaces = [Space(**r.data) for r in result.records]
        return spaces, total

    async def update_space(self, space_id: str, updates: dict[str, Any]) -> Space | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._space_repo.update(space_id, updates)

    async def get_building_hierarchy(self, building_id: str) -> dict[str, Any]:
        """Get full building hierarchy: building → floors → spaces."""
        building = await self._building_repo.get_by_id(building_id)
        if building is None:
            return {}
        floors, _ = await self.list_floors(building_id)
        hierarchy_floors = []
        for floor in floors:
            spaces, _ = await self.list_spaces(filters={"floor_id": floor.floor_id})
            hierarchy_floors.append({
                "floor": floor.model_dump(),
                "spaces": [s.model_dump() for s in spaces],
            })
        return {
            "building": building.model_dump(),
            "floors": hierarchy_floors,
        }
