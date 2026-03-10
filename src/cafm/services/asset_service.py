"""Service layer for asset management operations."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.assets import Asset, AssetLifecycleEvent
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class AssetService:
    """Business logic for asset management.

    Handles CRUD operations, QR code generation, lifecycle events,
    and asset intelligence queries.
    """

    def __init__(
        self,
        repository: Repository[Asset],
        event_bus: EventBus,
        lifecycle_repo: Repository[AssetLifecycleEvent] | None = None,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus
        self._lifecycle_repo = lifecycle_repo

    async def create_asset(self, data: dict[str, Any], created_by: str | None = None) -> Asset:
        """Create a new asset with auto-generated QR code."""
        now = datetime.utcnow()
        # Auto-generate QR code if not provided
        if not data.get("qr_code"):
            data["qr_code"] = f"AICMMS-{data['asset_id']}-{uuid.uuid4().hex[:8].upper()}"
        if not data.get("qr_code_url"):
            data["qr_code_url"] = f"/api/v1/assets/{data['asset_id']}/qr"

        data["created_at"] = now
        data["created_by"] = created_by

        asset = Asset(**data)
        created = await self._repo.create(asset)

        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED,
            source="asset_service",
            payload={"entity": "asset", "asset_id": created.asset_id},
        ))

        logger.info("Asset created: %s (%s)", created.asset_id, created.name)
        return created

    async def get_asset(self, asset_id: str) -> Asset | None:
        """Get a single asset by ID."""
        return await self._repo.get_by_id(asset_id)

    async def list_assets(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str | None = None,
    ) -> tuple[list[Asset], int]:
        """List assets with filtering and pagination.

        Returns (assets, total_count).
        """
        result_set = await self._repo.get_all(
            filters=filters, limit=limit, offset=offset, order_by=order_by,
        )
        total = await self._repo.count(filters=filters)
        # Extract domain models from result set records
        assets = []
        for record in result_set.records:
            if isinstance(record, Asset):
                assets.append(record)
            else:
                assets.append(Asset(**record.data if hasattr(record, "data") else {}))
        return assets, total

    async def update_asset(
        self, asset_id: str, updates: dict[str, Any], updated_by: str | None = None
    ) -> Asset | None:
        """Update an asset's fields."""
        updates["updated_at"] = datetime.utcnow()
        if updated_by:
            updates["updated_by"] = updated_by
        # Remove None values — only update fields that are explicitly set
        updates = {k: v for k, v in updates.items() if v is not None}

        updated = await self._repo.update(asset_id, updates)
        if updated:
            await self._event_bus.publish(Event(
                type=EventType.RECORD_UPDATED,
                source="asset_service",
                payload={"entity": "asset", "asset_id": asset_id},
            ))
        return updated

    async def delete_asset(self, asset_id: str, deleted_by: str | None = None) -> bool:
        """Soft-delete an asset."""
        result = await self._repo.update(asset_id, {
            "is_deleted": True,
            "deleted_at": datetime.utcnow(),
            "updated_by": deleted_by,
        })
        if result:
            await self._event_bus.publish(Event(
                type=EventType.RECORD_DELETED,
                source="asset_service",
                payload={"entity": "asset", "asset_id": asset_id},
            ))
        return result is not None

    async def get_asset_count(self, filters: dict[str, Any] | None = None) -> int:
        """Count assets matching filters."""
        return await self._repo.count(filters=filters)

    async def record_lifecycle_event(
        self,
        asset_id: str,
        event_type: str,
        description: str | None = None,
        performed_by: str | None = None,
        cost: float | None = None,
    ) -> AssetLifecycleEvent | None:
        """Record a lifecycle event for an asset."""
        if self._lifecycle_repo is None:
            logger.warning("Lifecycle repository not configured")
            return None

        event = AssetLifecycleEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            asset_id=asset_id,
            event_type=event_type,
            event_date=datetime.utcnow(),
            description=description,
            performed_by=performed_by,
            cost=cost,
        )
        return await self._lifecycle_repo.create(event)

    async def get_assets_by_facility(self, facility_id: str) -> tuple[list[Asset], int]:
        """Get all assets in a facility."""
        return await self.list_assets(filters={"facility_id": facility_id})

    async def get_critical_assets(self) -> tuple[list[Asset], int]:
        """Get assets with critical condition or criticality."""
        return await self.list_assets(filters={"criticality": "critical"})
