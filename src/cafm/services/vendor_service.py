"""Service layer for vendor and contract management (Story 11)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.vendors import Contract, ServiceLevel, Vendor
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class VendorService:
    """Business logic for vendor, contract, and SLA management."""

    def __init__(
        self,
        vendor_repo: Repository[Vendor],
        contract_repo: Repository[Contract],
        sla_repo: Repository[ServiceLevel],
        event_bus: EventBus,
    ) -> None:
        self._vendor_repo = vendor_repo
        self._contract_repo = contract_repo
        self._sla_repo = sla_repo
        self._event_bus = event_bus

    # ── Vendors ────────────────────────────────────────────────

    async def create_vendor(self, data: dict[str, Any], created_by: str | None = None) -> Vendor:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        vendor = Vendor(**data)
        created = await self._vendor_repo.create(vendor)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="vendor_service",
            payload={"entity": "vendor", "vendor_id": created.vendor_id},
        ))
        return created

    async def get_vendor(self, vendor_id: str) -> Vendor | None:
        return await self._vendor_repo.get_by_id(vendor_id)

    async def list_vendors(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Vendor], int]:
        result = await self._vendor_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._vendor_repo.count(filters=filters)
        vendors = [Vendor(**r.data) for r in result.records]
        return vendors, total

    async def update_vendor(
        self, vendor_id: str, updates: dict[str, Any], updated_by: str | None = None,
    ) -> Vendor | None:
        updates["updated_at"] = datetime.utcnow()
        if updated_by:
            updates["updated_by"] = updated_by
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._vendor_repo.update(vendor_id, updates)

    async def delete_vendor(self, vendor_id: str) -> bool:
        return await self._vendor_repo.delete(vendor_id)

    # ── Contracts ──────────────────────────────────────────────

    async def create_contract(self, data: dict[str, Any], created_by: str | None = None) -> Contract:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        contract = Contract(**data)
        return await self._contract_repo.create(contract)

    async def get_contract(self, contract_id: str) -> Contract | None:
        return await self._contract_repo.get_by_id(contract_id)

    async def list_contracts(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[Contract], int]:
        result = await self._contract_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._contract_repo.count(filters=filters)
        contracts = [Contract(**r.data) for r in result.records]
        return contracts, total

    async def get_vendor_contracts(self, vendor_id: str) -> tuple[list[Contract], int]:
        return await self.list_contracts(filters={"vendor_id": vendor_id})

    async def update_contract(
        self, contract_id: str, updates: dict[str, Any],
    ) -> Contract | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._contract_repo.update(contract_id, updates)

    # ── SLAs ───────────────────────────────────────────────────

    async def create_sla(self, data: dict[str, Any]) -> ServiceLevel:
        sla = ServiceLevel(**data)
        return await self._sla_repo.create(sla)

    async def get_contract_slas(self, contract_id: str) -> tuple[list[ServiceLevel], int]:
        result = await self._sla_repo.get_all(filters={"contract_id": contract_id})
        total = await self._sla_repo.count(filters={"contract_id": contract_id})
        slas = [ServiceLevel(**r.data) for r in result.records]
        return slas, total

    async def get_vendor_performance(self, vendor_id: str) -> dict[str, Any]:
        """Calculate vendor performance metrics."""
        vendor = await self._vendor_repo.get_by_id(vendor_id)
        contracts, contract_count = await self.get_vendor_contracts(vendor_id)
        active_contracts = [c for c in contracts if c.status == "active"]
        total_value = sum(c.total_value or 0 for c in active_contracts)
        return {
            "vendor_id": vendor_id,
            "vendor_name": vendor.name if vendor else "Unknown",
            "total_contracts": contract_count,
            "active_contracts": len(active_contracts),
            "total_contract_value": total_value,
            "rating": vendor.rating if vendor else None,
        }
