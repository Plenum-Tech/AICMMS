"""Tests for newly added API schemas — vendors, inspections, costs,
sensors, documents, gamification, occupancy, query.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from cafm.api.schemas.costs import (
    BudgetResponse, CostCenterResponse, ExpenseCreateRequest,
    ExpenseResponse, InvoiceCreateRequest, InvoiceResponse,
    InvoiceUpdateRequest, WOCommercialJourney,
)
from cafm.api.schemas.documents import (
    DocTemplateCreateRequest, DocTemplateResponse,
    ExcelTemplateCreateRequest, ExcelTemplateImportRequest, ExcelTemplateResponse,
    GenerateDocumentRequest, GeneratedDocumentResponse,
    ReportScheduleCreateRequest, ReportScheduleResponse,
)
from cafm.api.schemas.gamification import (
    AssetInsightCreateRequest, AssetInsightResponse,
    BadgeResponse, GamificationProfileResponse,
    LeaderboardEntry, OccupancyResponse, PointTransactionResponse,
    QueryInterfaceRequest, QueryInterfaceResponse,
    ReservationCreateRequest, ReservationResponse,
    SpaceUtilizationResponse,
)
from cafm.api.schemas.sensors import (
    DeviceCreateRequest, DeviceResponse,
    SensorReadingInput, SensorReadingResponse,
    ThresholdResponse,
)
from cafm.api.schemas.vendors import (
    ContractCreateRequest, ContractResponse,
    SLACreateRequest, SLAResponse,
    VendorCreateRequest, VendorResponse, VendorUpdateRequest,
)


class TestVendorSchemas:
    def test_vendor_create_request(self):
        req = VendorCreateRequest(
            vendor_id="VND-001", name="HVAC Solutions",
            vendor_type="hvac", email="vendor@test.com",
        )
        assert req.vendor_id == "VND-001"
        assert req.vendor_type == "hvac"

    def test_vendor_response(self):
        resp = VendorResponse(
            vendor_id="VND-001", name="Test",
            vendor_type="hvac", is_active=True,
        )
        assert resp.is_active is True

    def test_contract_create_request(self):
        req = ContractCreateRequest(
            contract_id="CON-001", vendor_id="VND-001",
            title="Service Agreement", contract_type="service",
        )
        assert req.contract_id == "CON-001"

    def test_sla_create_request(self):
        req = SLACreateRequest(
            sla_id="SLA-001", contract_id="CON-001",
            metric_name="Response Time",
            target_value=4.0, unit="hours",
        )
        assert req.target_value == 4.0


class TestCostSchemas:
    def test_expense_create_request(self):
        req = ExpenseCreateRequest(
            expense_id="EXP-001", cost_center_id="CC-001",
            category="maintenance", amount=500.0,
            expense_date=date(2024, 1, 15),
        )
        assert req.amount == 500.0

    def test_invoice_create_request(self):
        req = InvoiceCreateRequest(
            invoice_id="INV-001", vendor_id="VND-001",
            invoice_number="INV-2024-001", amount=1500.0,
            issue_date=date(2024, 1, 1),
        )
        assert req.currency == "USD"

    def test_wo_commercial_journey(self):
        journey = WOCommercialJourney(
            work_order_id="WO-001",
            work_order_title="Fix HVAC",
            work_order_status="completed",
            has_breakage=True,
            breakage_details=["No invoice generated"],
        )
        assert journey.has_breakage is True
        assert len(journey.breakage_details) == 1

    def test_budget_response(self):
        resp = BudgetResponse(
            budget_id="BUD-001", cost_center_id="CC-001",
            fiscal_year=2024, allocated_amount=50000.0,
            spent_amount=20000.0, committed_amount=5000.0,
            remaining=25000.0, utilization_pct=50.0,
        )
        assert resp.remaining == 25000.0


class TestSensorSchemas:
    def test_device_create_request(self):
        req = DeviceCreateRequest(
            device_id="DEV-001", name="Temp Sensor",
            device_type="temperature",
        )
        assert req.device_type == "temperature"

    def test_sensor_reading_input(self):
        reading = SensorReadingInput(
            device_id="DEV-001", value=23.5, unit="celsius",
        )
        assert reading.value == 23.5
        assert reading.quality == "good"

    def test_threshold_response(self):
        resp = ThresholdResponse(
            threshold_id="TH-001", device_id="DEV-001",
            metric="temperature", min_value=15.0,
            max_value=35.0, alert_severity="warning",
        )
        assert resp.is_active is True


class TestDocumentSchemas:
    def test_doc_template_create(self):
        req = DocTemplateCreateRequest(
            template_id="TPL-001", name="Inspection Report",
            template_type="report",
        )
        assert req.template_type == "report"

    def test_generate_document_request(self):
        req = GenerateDocumentRequest(
            template_id="TPL-001", title="Weekly Report",
            content={"section1": "data"},
        )
        assert req.title == "Weekly Report"

    def test_report_schedule_create(self):
        req = ReportScheduleCreateRequest(
            schedule_id="RS-001", template_id="TPL-001",
            name="Weekly Safety Report", query_text="safety inspections this week",
            frequency="weekly", day_of_week=1,
        )
        assert req.frequency == "weekly"

    def test_excel_template_create(self):
        req = ExcelTemplateCreateRequest(
            template_id="XLS-001", name="Asset Register",
        )
        assert req.template_id == "XLS-001"

    def test_excel_template_import(self):
        req = ExcelTemplateImportRequest(
            name="Imported Template",
            file_url="/uploads/template.xlsx",
        )
        assert req.file_url == "/uploads/template.xlsx"


class TestGamificationSchemas:
    def test_profile_response(self):
        resp = GamificationProfileResponse(
            profile_id="GP-001", technician_id="TECH-001",
            total_points=500, impact_points=100,
            current_level=3, level_name="Specialist",
        )
        assert resp.level_name == "Specialist"

    def test_leaderboard_entry(self):
        entry = LeaderboardEntry(
            rank=1, technician_id="TECH-001",
            technician_name="John", total_points=1000,
            impact_points=200, level=4, level_name="Expert",
        )
        assert entry.rank == 1

    def test_asset_insight_create(self):
        req = AssetInsightCreateRequest(
            asset_id="AST-001", insight_text="Bearing noise detected",
        )
        assert req.insight_text == "Bearing noise detected"

    def test_query_interface_request(self):
        req = QueryInterfaceRequest(
            query_text="Show overdue work orders",
            query_type="text",
        )
        assert req.query_type == "text"

    def test_reservation_create(self):
        req = ReservationCreateRequest(
            reservation_id="RES-001", space_id="SPC-001",
            building_id="BLD-001", reserved_by="USER-001",
            start_time=datetime(2024, 3, 15, 9, 0),
            end_time=datetime(2024, 3, 15, 11, 0),
        )
        assert req.space_id == "SPC-001"

    def test_occupancy_response(self):
        resp = OccupancyResponse(
            space_id="SPC-001", building_id="BLD-001",
            timestamp=datetime(2024, 3, 15, 10, 0),
            occupant_count=25, capacity=50,
            utilization_pct=50.0,
        )
        assert resp.utilization_pct == 50.0
