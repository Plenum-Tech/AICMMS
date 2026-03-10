"""Tests for service layer business logic."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from cafm.core.events import EventBus
from cafm.domain.assets import Asset
from cafm.domain.enums import (
    AssetCondition,
    AssetCriticality,
    AssetStatus,
    WorkOrderPriority,
    WorkOrderStatus,
)
from cafm.domain.technicians import Technician
from cafm.domain.work_orders import WorkOrder
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.services.asset_service import AssetService
from cafm.services.work_order_service import WorkOrderService
from cafm.services.technician_service import TechnicianService


# ── Mock Repository ───────────────────────────────────────────────


class MockRepository:
    """In-memory mock repository for testing services."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._id_field: str = "asset_id"

    def set_id_field(self, field: str) -> None:
        self._id_field = field

    async def get_by_id(self, entity_id: str):
        return self._store.get(entity_id)

    async def get_all(self, filters=None, limit=None, offset=0, order_by=None):
        items = list(self._store.values())
        if filters:
            for key, val in filters.items():
                items = [i for i in items if getattr(i, key, None) == val]
        # Wrap domain models as UnifiedRecords for ResultSet compatibility
        meta = RecordMetadata(source_name="mock", source_type="csv", table_name="mock")
        records = [UnifiedRecord(data=item.model_dump(), metadata=meta) for item in items]
        return UnifiedResultSet(records=records, total_count=len(items), offset=offset, limit=limit or 50)

    async def create(self, entity):
        entity_id = getattr(entity, self._id_field)
        self._store[entity_id] = entity
        return entity

    async def update(self, entity_id: str, updates: dict):
        entity = self._store.get(entity_id)
        if entity is None:
            return None
        for key, val in updates.items():
            if hasattr(entity, key):
                object.__setattr__(entity, key, val)
        self._store[entity_id] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        return self._store.pop(entity_id, None) is not None

    async def count(self, filters=None) -> int:
        if not filters:
            return len(self._store)
        items = list(self._store.values())
        for key, val in filters.items():
            items = [i for i in items if getattr(i, key, None) == val]
        return len(items)

    async def bulk_create(self, entities):
        for e in entities:
            await self.create(e)
        return entities

    async def bulk_update(self, updates):
        count = 0
        for eid, upd in updates:
            if await self.update(eid, upd):
                count += 1
        return count


# ── Asset Service Tests ───────────────────────────────────────────


class TestAssetService:
    @pytest.fixture
    def asset_service(self):
        repo = MockRepository()
        repo.set_id_field("asset_id")
        bus = EventBus()
        return AssetService(repository=repo, event_bus=bus)

    async def test_create_asset_generates_qr(self, asset_service):
        asset = await asset_service.create_asset({
            "asset_id": "AST-001",
            "name": "Test HVAC",
            "category": "hvac",
            "facility_id": "BLD-001",
        })
        assert asset.asset_id == "AST-001"
        assert asset.qr_code is not None
        assert asset.qr_code.startswith("AICMMS-AST-001-")
        assert asset.qr_code_url == "/api/v1/assets/AST-001/qr"

    async def test_get_asset(self, asset_service):
        await asset_service.create_asset({
            "asset_id": "AST-002",
            "name": "Elevator",
            "category": "elevator",
            "facility_id": "BLD-001",
        })
        asset = await asset_service.get_asset("AST-002")
        assert asset is not None
        assert asset.name == "Elevator"

    async def test_get_nonexistent_asset(self, asset_service):
        asset = await asset_service.get_asset("NOPE")
        assert asset is None

    async def test_update_asset(self, asset_service):
        await asset_service.create_asset({
            "asset_id": "AST-003",
            "name": "Old Name",
            "category": "hvac",
            "facility_id": "BLD-001",
        })
        updated = await asset_service.update_asset("AST-003", {"name": "New Name"})
        assert updated is not None
        assert updated.name == "New Name"

    async def test_delete_asset(self, asset_service):
        await asset_service.create_asset({
            "asset_id": "AST-004",
            "name": "To Delete",
            "category": "hvac",
            "facility_id": "BLD-001",
        })
        deleted = await asset_service.delete_asset("AST-004")
        assert deleted is True

    async def test_count_assets(self, asset_service):
        await asset_service.create_asset({
            "asset_id": "AST-005", "name": "A", "category": "hvac", "facility_id": "BLD-001",
        })
        await asset_service.create_asset({
            "asset_id": "AST-006", "name": "B", "category": "hvac", "facility_id": "BLD-001",
        })
        count = await asset_service.get_asset_count()
        assert count == 2


# ── Work Order Service Tests ──────────────────────────────────────


class TestWorkOrderService:
    @pytest.fixture
    def wo_service(self):
        repo = MockRepository()
        repo.set_id_field("work_order_id")
        bus = EventBus()
        return WorkOrderService(repository=repo, event_bus=bus)

    async def test_create_work_order(self, wo_service):
        wo = await wo_service.create_work_order({
            "work_order_id": "WO-001",
            "title": "Fix AC",
        })
        assert wo.work_order_id == "WO-001"
        assert wo.status == WorkOrderStatus.SUBMITTED

    async def test_create_adhoc_work_order(self, wo_service):
        wo = await wo_service.create_adhoc_work_order(
            text="The elevator on floor 3 is stuck",
            building_id="BLD-001",
            priority=WorkOrderPriority.HIGH,
        )
        assert wo.work_order_id.startswith("WO-")
        assert "elevator" in wo.description.lower()
        assert wo.priority == WorkOrderPriority.HIGH

    async def test_transition_status(self, wo_service):
        await wo_service.create_work_order({
            "work_order_id": "WO-002",
            "title": "Test Transition",
            "status": WorkOrderStatus.SUBMITTED,
        })
        wo = await wo_service.transition_status("WO-002", WorkOrderStatus.APPROVED)
        assert wo is not None
        assert wo.status == WorkOrderStatus.APPROVED

    async def test_invalid_transition_raises(self, wo_service):
        await wo_service.create_work_order({
            "work_order_id": "WO-003",
            "title": "Test Invalid",
            "status": WorkOrderStatus.SUBMITTED,
        })
        with pytest.raises(ValueError, match="Cannot transition"):
            await wo_service.transition_status("WO-003", WorkOrderStatus.CLOSED)

    async def test_assign_work_order(self, wo_service):
        await wo_service.create_work_order({
            "work_order_id": "WO-004",
            "title": "Assign Test",
        })
        wo = await wo_service.assign_work_order("WO-004", "TECH-001")
        assert wo is not None
        assert wo.assigned_to == "TECH-001"


# ── Technician Service Tests ──────────────────────────────────────


class TestTechnicianService:
    @pytest.fixture
    def tech_service(self):
        repo = MockRepository()
        repo.set_id_field("technician_id")
        bus = EventBus()
        return TechnicianService(repository=repo, event_bus=bus)

    async def test_create_technician(self, tech_service):
        tech = await tech_service.create_technician({
            "technician_id": "TECH-001",
            "first_name": "John",
            "last_name": "Doe",
            "skill_codes": ["hvac", "electrical"],
        })
        assert tech.technician_id == "TECH-001"
        assert "hvac" in tech.skill_codes

    async def test_get_available_technicians(self, tech_service):
        await tech_service.create_technician({
            "technician_id": "TECH-002",
            "first_name": "Jane",
            "last_name": "Smith",
            "skill_codes": ["hvac"],
            "is_available": True,
        })
        await tech_service.create_technician({
            "technician_id": "TECH-003",
            "first_name": "Bob",
            "last_name": "Jones",
            "skill_codes": ["plumbing"],
            "is_available": False,
        })
        available = await tech_service.get_available_technicians(skill_codes=["hvac"])
        assert len(available) == 1
        assert available[0].technician_id == "TECH-002"

    async def test_recommend_technician(self, tech_service):
        await tech_service.create_technician({
            "technician_id": "TECH-004",
            "first_name": "Expert",
            "last_name": "Tech",
            "skill_codes": ["hvac", "electrical"],
            "is_available": True,
            "experience_years": 10,
            "customer_satisfaction_avg": 4.8,
            "current_workload_count": 1,
        })
        await tech_service.create_technician({
            "technician_id": "TECH-005",
            "first_name": "Junior",
            "last_name": "Tech",
            "skill_codes": ["hvac"],
            "is_available": True,
            "experience_years": 1,
            "customer_satisfaction_avg": 3.5,
            "current_workload_count": 5,
        })
        recs = await tech_service.recommend_technician(required_skills=["hvac"])
        assert len(recs) == 2
        # Expert should rank higher
        assert recs[0]["technician_id"] == "TECH-004"
        assert recs[0]["match_score"] > recs[1]["match_score"]

    async def test_award_points(self, tech_service):
        await tech_service.create_technician({
            "technician_id": "TECH-006",
            "first_name": "Gamer",
            "last_name": "Tech",
            "gamification_points": 50,
            "gamification_level": 1,
        })
        tech = await tech_service.award_points("TECH-006", 60)
        assert tech is not None
        assert tech.gamification_points == 110
        assert tech.gamification_level == 2  # 110 // 100 + 1
