"""Tests for newly added services — vendors, inspections, maintenance,
facilities, documents, costs, gamification, sensors, query, occupancy.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pytest

from cafm.core.events import EventBus
from cafm.domain.costs import Budget, CostCenter, Expense, Invoice
from cafm.domain.facilities import Building, Floor, Space
from cafm.domain.gamification import Badge, GamificationProfile, PointTransaction
from cafm.domain.inspections import InspectionReport
from cafm.domain.maintenance import FailureMode, MaintenanceLog, MaintenanceSchedule
from cafm.domain.occupancy import OccupancyData, Reservation, SpaceUtilization
from cafm.domain.sensors import IoTDevice, SensorReading, Threshold
from cafm.domain.vendors import Contract, Vendor
from cafm.models.record import RecordMetadata, UnifiedRecord
from cafm.models.resultset import UnifiedResultSet
from cafm.services.cost_service import CostService
from cafm.services.facility_service import FacilityService
from cafm.services.gamification_service import GamificationService
from cafm.services.inspection_service import InspectionService
from cafm.services.maintenance_service import MaintenanceService
from cafm.services.occupancy_service import OccupancyService
from cafm.services.query_service import QueryService
from cafm.services.sensor_service import SensorService
from cafm.services.vendor_service import VendorService


# ── Mock Repository ───────────────────────────────────────────────


class MockRepo:
    """In-memory mock repository for testing services."""

    def __init__(self, id_field: str = "id") -> None:
        self._store: dict[str, Any] = {}
        self._id_field = id_field

    async def get_by_id(self, entity_id: str):
        return self._store.get(entity_id)

    async def get_all(self, filters=None, limit=None, offset=0, order_by=None):
        items = list(self._store.values())
        if filters:
            for key, val in filters.items():
                items = [i for i in items if getattr(i, key, None) == val]
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


# ── Vendor Service Tests ──────────────────────────────────────────


class TestVendorService:
    @pytest.fixture
    def vendor_service(self):
        return VendorService(
            vendor_repo=MockRepo("vendor_id"),
            contract_repo=MockRepo("contract_id"),
            sla_repo=MockRepo("sla_id"),
            event_bus=EventBus(),
        )

    async def test_create_vendor(self, vendor_service):
        vendor = await vendor_service.create_vendor({
            "vendor_id": "VND-001",
            "name": "HVAC Solutions",
            "vendor_type": "hvac",
        })
        assert vendor.vendor_id == "VND-001"
        assert vendor.name == "HVAC Solutions"

    async def test_get_vendor(self, vendor_service):
        await vendor_service.create_vendor({
            "vendor_id": "VND-002", "name": "Test", "vendor_type": "hvac",
        })
        vendor = await vendor_service.get_vendor("VND-002")
        assert vendor is not None
        assert vendor.name == "Test"

    async def test_list_vendors(self, vendor_service):
        await vendor_service.create_vendor({"vendor_id": "VND-A", "name": "A", "vendor_type": "hvac"})
        await vendor_service.create_vendor({"vendor_id": "VND-B", "name": "B", "vendor_type": "electrical"})
        vendors, total = await vendor_service.list_vendors()
        assert total == 2

    async def test_create_contract(self, vendor_service):
        contract = await vendor_service.create_contract({
            "contract_id": "CON-001", "vendor_id": "VND-001",
            "title": "Annual HVAC Service", "contract_type": "fixed_price",
        })
        assert contract.contract_id == "CON-001"


# ── Inspection Service Tests ──────────────────────────────────────


class TestInspectionService:
    @pytest.fixture
    def inspection_service(self):
        return InspectionService(
            inspection_repo=MockRepo("report_id"),
            insight_repo=MockRepo("insight_id"),
            event_bus=EventBus(),
        )

    async def test_create_inspection(self, inspection_service):
        report = await inspection_service.create_inspection({
            "report_id": "INS-001",
            "asset_id": "AST-001",
            "inspection_type": "routine",
            "inspector_id": "TECH-001",
        }, inspector_id="TECH-001")
        assert report.report_id == "INS-001"

    async def test_get_inspection(self, inspection_service):
        await inspection_service.create_inspection({
            "report_id": "INS-002", "asset_id": "AST-001",
            "inspection_type": "safety", "inspector_id": "TECH-001",
        }, inspector_id="TECH-001")
        report = await inspection_service.get_inspection("INS-002")
        assert report is not None

    async def test_classify_inspection(self, inspection_service):
        await inspection_service.create_inspection({
            "report_id": "INS-003", "asset_id": "AST-001",
            "inspection_type": "routine", "inspector_id": "TECH-001",
        }, inspector_id="TECH-001")
        result = await inspection_service.classify_inspection("INS-003")
        assert "classification" in result
        assert "confidence" in result["classification"]


# ── Maintenance Service Tests ─────────────────────────────────────


class TestMaintenanceService:
    @pytest.fixture
    def maint_service(self):
        return MaintenanceService(
            schedule_repo=MockRepo("schedule_id"),
            log_repo=MockRepo("log_id"),
            failure_mode_repo=MockRepo("mode_id"),
            event_bus=EventBus(),
        )

    async def test_create_schedule(self, maint_service):
        schedule = await maint_service.create_schedule({
            "schedule_id": "SCH-001",
            "asset_id": "AST-001",
            "name": "Monthly HVAC Check",
            "frequency": "monthly",
        })
        assert schedule.schedule_id == "SCH-001"
        assert schedule.next_due is not None

    async def test_get_upcoming_ppm(self, maint_service):
        await maint_service.create_schedule({
            "schedule_id": "SCH-002",
            "asset_id": "AST-001",
            "name": "Due Soon",
            "frequency": "weekly",
            "is_active": True,
            "next_due": datetime.utcnow() + timedelta(days=5),
        })
        upcoming = await maint_service.get_upcoming_ppm(days_ahead=7)
        assert len(upcoming) == 1

    async def test_get_overdue_ppm(self, maint_service):
        await maint_service.create_schedule({
            "schedule_id": "SCH-003",
            "asset_id": "AST-001",
            "name": "Overdue",
            "frequency": "daily",
            "is_active": True,
            "next_due": datetime.utcnow() - timedelta(days=2),
        })
        overdue = await maint_service.get_overdue_ppm()
        assert len(overdue) == 1

    async def test_generate_ppm_insights(self, maint_service):
        insights = await maint_service.generate_ppm_insights("AST-001")
        assert "risk_score" in insights
        assert "recommended_action" in insights


# ── Facility Service Tests ────────────────────────────────────────


class TestFacilityService:
    @pytest.fixture
    def facility_service(self):
        return FacilityService(
            building_repo=MockRepo("building_id"),
            floor_repo=MockRepo("floor_id"),
            space_repo=MockRepo("space_id"),
            event_bus=EventBus(),
        )

    async def test_create_building(self, facility_service):
        building = await facility_service.create_building({
            "building_id": "BLD-001",
            "name": "Main Office",
            "address": "123 Main St",
        })
        assert building.building_id == "BLD-001"

    async def test_list_buildings(self, facility_service):
        await facility_service.create_building({"building_id": "BLD-A", "name": "A"})
        await facility_service.create_building({"building_id": "BLD-B", "name": "B"})
        buildings, total = await facility_service.list_buildings()
        assert total == 2

    async def test_get_building(self, facility_service):
        await facility_service.create_building({"building_id": "BLD-X", "name": "X"})
        building = await facility_service.get_building("BLD-X")
        assert building is not None
        assert building.name == "X"


# ── Cost Service Tests ────────────────────────────────────────────


class TestCostService:
    @pytest.fixture
    def cost_service(self):
        return CostService(
            expense_repo=MockRepo("expense_id"),
            invoice_repo=MockRepo("invoice_id"),
            budget_repo=MockRepo("budget_id"),
            cost_center_repo=MockRepo("cost_center_id"),
            event_bus=EventBus(),
        )

    async def test_create_expense(self, cost_service):
        expense = await cost_service.create_expense({
            "expense_id": "EXP-001",
            "cost_center_id": "CC-001",
            "category": "maintenance",
            "amount": 500.0,
            "expense_date": date(2024, 1, 15),
        })
        assert expense.expense_id == "EXP-001"
        assert expense.amount == 500.0

    async def test_create_invoice(self, cost_service):
        invoice = await cost_service.create_invoice({
            "invoice_id": "INV-001",
            "vendor_id": "VND-001",
            "invoice_number": "INV-2024-001",
            "amount": 1500.0,
            "issue_date": date(2024, 1, 1),
        })
        assert invoice.invoice_id == "INV-001"

    async def test_get_invoice(self, cost_service):
        await cost_service.create_invoice({
            "invoice_id": "INV-002",
            "vendor_id": "VND-001",
            "invoice_number": "INV-2024-002",
            "amount": 2500.0,
            "issue_date": date(2024, 1, 1),
        })
        invoice = await cost_service.get_invoice("INV-002")
        assert invoice is not None
        assert invoice.amount == 2500.0

    async def test_get_cost_summary(self, cost_service):
        await cost_service.create_expense({
            "expense_id": "EXP-A", "cost_center_id": "CC-001",
            "category": "repair", "amount": 100.0,
            "expense_date": date(2024, 1, 15),
        })
        await cost_service.create_invoice({
            "invoice_id": "INV-A", "vendor_id": "VND-A",
            "invoice_number": "NUM-A", "amount": 200.0, "status": "pending",
            "issue_date": date(2024, 1, 1),
        })
        summary = await cost_service.get_cost_summary()
        assert summary["total_expenses"] == 1
        assert summary["total_invoices"] == 1
        assert summary["total_spent"] == 100.0


# ── Gamification Service Tests ────────────────────────────────────


class TestGamificationService:
    @pytest.fixture
    def gam_service(self):
        return GamificationService(
            profile_repo=MockRepo("profile_id"),
            transaction_repo=MockRepo("transaction_id"),
            badge_repo=MockRepo("badge_id"),
            event_bus=EventBus(),
        )

    async def test_get_or_create_profile(self, gam_service):
        profile = await gam_service.get_or_create_profile("TECH-001")
        assert profile.technician_id == "TECH-001"
        assert profile.total_points == 0
        assert profile.level_name == "Rookie"

    async def test_award_points(self, gam_service):
        await gam_service.get_or_create_profile("TECH-002")
        tx = await gam_service.award_points(
            technician_id="TECH-002",
            points=150,
            point_type="inspection",
            reason="Completed 10 inspections",
        )
        assert tx.points == 150
        profile = await gam_service.get_profile("TECH-002")
        assert profile.total_points == 150
        assert profile.current_level == 2  # 150 >= 100 → Apprentice (level 2)

    async def test_leaderboard(self, gam_service):
        await gam_service.get_or_create_profile("TECH-A")
        await gam_service.award_points("TECH-A", 500, "inspection", "test")
        await gam_service.get_or_create_profile("TECH-B")
        await gam_service.award_points("TECH-B", 200, "inspection", "test")
        board = await gam_service.get_leaderboard(top_n=10)
        assert len(board) == 2
        assert board[0]["technician_id"] == "TECH-A"
        assert board[0]["rank"] == 1

    async def test_level_calculation(self, gam_service):
        # Test static method
        assert GamificationService._calculate_level(0) == (1, "Rookie")
        assert GamificationService._calculate_level(100) == (2, "Apprentice")
        assert GamificationService._calculate_level(500) == (3, "Specialist")
        assert GamificationService._calculate_level(1500) == (4, "Expert")
        assert GamificationService._calculate_level(5000) == (5, "Master")
        assert GamificationService._calculate_level(15000) == (6, "Legend")


# ── Sensor Service Tests ──────────────────────────────────────────


class TestSensorService:
    @pytest.fixture
    def sensor_service(self):
        return SensorService(
            device_repo=MockRepo("device_id"),
            reading_repo=MockRepo("reading_id"),
            threshold_repo=MockRepo("threshold_id"),
            event_bus=EventBus(),
        )

    async def test_create_device(self, sensor_service):
        device = await sensor_service.create_device({
            "device_id": "DEV-001",
            "name": "Temperature Sensor",
            "device_type": "temperature",
        })
        assert device.device_id == "DEV-001"

    async def test_ingest_reading(self, sensor_service):
        await sensor_service.create_device({
            "device_id": "DEV-002",
            "name": "Humidity Sensor",
            "device_type": "humidity",
        })
        reading = await sensor_service.ingest_reading({
            "device_id": "DEV-002",
            "value": 65.5,
            "unit": "percent",
        })
        assert reading.value == 65.5
        assert reading.reading_id.startswith("SR-")

    async def test_ingest_batch(self, sensor_service):
        await sensor_service.create_device({
            "device_id": "DEV-003", "name": "Multi", "device_type": "temperature",
        })
        results = await sensor_service.ingest_readings_batch([
            {"device_id": "DEV-003", "value": 22.1},
            {"device_id": "DEV-003", "value": 22.3},
            {"device_id": "DEV-003", "value": 22.5},
        ])
        assert len(results) == 3

    async def test_threshold_breach(self, sensor_service):
        # Create device and threshold
        await sensor_service.create_device({
            "device_id": "DEV-004", "name": "Temp", "device_type": "temperature",
        })
        await sensor_service._threshold_repo.create(Threshold(
            threshold_id="TH-001", device_id="DEV-004",
            metric="temperature", min_value=15.0, max_value=30.0,
            alert_severity="critical", is_active=True,
        ))
        # Normal reading
        normal = await sensor_service.ingest_reading({"device_id": "DEV-004", "value": 25.0})
        assert normal.is_anomaly is False
        # Breach reading
        breach = await sensor_service.ingest_reading({"device_id": "DEV-004", "value": 35.0})
        assert breach.is_anomaly is True


# ── Query Service Tests ───────────────────────────────────────────


class TestQueryService:
    @pytest.fixture
    def query_service(self):
        return QueryService(event_bus=EventBus())

    async def test_process_query(self, query_service):
        result = await query_service.process_query(
            query_text="Show me overdue work orders",
            user_id="USER-001",
        )
        assert "query_id" in result
        assert "response_text" in result
        assert result["confidence"] > 0

    async def test_query_history(self, query_service):
        await query_service.process_query("Query 1", user_id="USER-002")
        await query_service.process_query("Query 2", user_id="USER-002")
        history = await query_service.get_query_history("USER-002")
        assert len(history) == 2

    async def test_suggestions(self, query_service):
        suggestions = await query_service.get_suggestions("USER-001")
        assert len(suggestions) > 0
        assert all("query" in s for s in suggestions)

    async def test_contextual_suggestions(self, query_service):
        dashboard_suggestions = await query_service.get_suggestions("USER-001", context="dashboard")
        assert dashboard_suggestions[0]["category"] == "dashboard"


# ── Occupancy Service Tests ───────────────────────────────────────


class TestOccupancyService:
    @pytest.fixture
    def occ_service(self):
        return OccupancyService(
            occupancy_repo=MockRepo("reading_id"),
            utilization_repo=MockRepo("space_id"),
            reservation_repo=MockRepo("reservation_id"),
            event_bus=EventBus(),
        )

    async def test_create_reservation(self, occ_service):
        reservation = await occ_service.create_reservation({
            "reservation_id": "RES-001",
            "space_id": "SPC-001",
            "building_id": "BLD-001",
            "reserved_by": "USER-001",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=2),
        })
        assert reservation.reservation_id == "RES-001"
        assert reservation.status == "confirmed"

    async def test_cancel_reservation(self, occ_service):
        await occ_service.create_reservation({
            "reservation_id": "RES-002",
            "space_id": "SPC-001",
            "building_id": "BLD-001",
            "reserved_by": "USER-001",
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow() + timedelta(hours=1),
        })
        cancelled = await occ_service.cancel_reservation("RES-002", cancelled_by="USER-001")
        assert cancelled is not None
        assert cancelled.status == "cancelled"

    async def test_get_heatmap(self, occ_service):
        heatmap = await occ_service.get_heatmap(building_id="BLD-001")
        assert heatmap["building_id"] == "BLD-001"
        assert "spaces" in heatmap
        assert "timestamp" in heatmap
