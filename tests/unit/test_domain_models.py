"""Tests for CAFM domain models."""

from cafm.domain.assets import Asset, AssetCategory
from cafm.domain.enums import AssetCondition, AssetStatus, WorkOrderPriority, WorkOrderStatus
from cafm.domain.facilities import Building, Floor, Space
from cafm.domain.work_orders import WorkOrder
from cafm.domain.maintenance import MaintenanceSchedule
from cafm.domain.vendors import Vendor, Contract
from cafm.domain.sensors import IoTDevice, SensorReading
from cafm.domain.costs import Budget
from cafm.domain.technicians import Technician
from cafm.domain.inspections import InspectionReport
from cafm.domain.documents import DocumentTemplate, ReportSchedule
from cafm.domain.gamification import GamificationProfile, AssetInsight


def test_asset_creation():
    asset = Asset(
        asset_id="HVAC-001",
        name="Rooftop AC Unit 1",
        category="HVAC",
        facility_id="BLDG-A",
        status=AssetStatus.ACTIVE,
        condition=AssetCondition.GOOD,
    )
    assert asset.asset_id == "HVAC-001"
    assert asset.status == AssetStatus.ACTIVE
    assert asset.qr_code is None
    assert asset.failure_count == 0


def test_asset_with_qr_code():
    asset = Asset(
        asset_id="PUMP-001",
        name="Water Pump",
        category="plumbing",
        facility_id="BLDG-B",
        qr_code="QR-PUMP-001-ABC",
        qr_code_url="https://example.com/qr/PUMP-001.png",
        onboarding_method="image_detection",
    )
    assert asset.qr_code == "QR-PUMP-001-ABC"
    assert asset.onboarding_method == "image_detection"


def test_building_creation():
    bldg = Building(
        building_id="BLDG-A",
        name="Main Office Tower",
        city="Dubai",
        country="UAE",
        floor_count=25,
    )
    assert bldg.building_id == "BLDG-A"
    assert bldg.floor_count == 25


def test_work_order_creation():
    wo = WorkOrder(
        work_order_id="WO-001",
        title="Fix AC leak",
        priority=WorkOrderPriority.HIGH,
        status=WorkOrderStatus.SUBMITTED,
        asset_id="HVAC-001",
    )
    assert wo.priority == WorkOrderPriority.HIGH
    assert wo.status == WorkOrderStatus.SUBMITTED


def test_technician_creation():
    tech = Technician(
        technician_id="TECH-001",
        first_name="Ahmed",
        last_name="Khan",
        skill_codes=["HVAC", "electrical"],
        gamification_points=250,
        gamification_level=3,
    )
    assert tech.technician_id == "TECH-001"
    assert "HVAC" in tech.skill_codes
    assert tech.gamification_points == 250


def test_inspection_report_creation():
    report = InspectionReport(
        report_id="IR-001",
        asset_id="HVAC-001",
        inspection_type="ppm",
        inspector_id="TECH-001",
        inspection_date="2026-03-09T10:00:00",
        photo_urls=["https://example.com/photo1.jpg"],
        voice_note_urls=["https://example.com/voice1.mp3"],
        points_earned=10,
    )
    assert report.inspection_type == "ppm"
    assert len(report.photo_urls) == 1
    assert report.points_earned == 10


def test_gamification_profile():
    profile = GamificationProfile(
        profile_id="GP-001",
        technician_id="TECH-001",
        total_points=500,
        impact_points=120,
        current_level=4,
        level_name="Expert",
    )
    assert profile.current_level == 4
    assert profile.level_name == "Expert"


def test_asset_insight():
    insight = AssetInsight(
        insight_id="INS-001",
        technician_id="TECH-001",
        asset_id="HVAC-001",
        insight_text="Compressor vibration increasing, may need replacement soon",
        scanned_qr_code="QR-HVAC-001",
        ai_category="maintenance_needed",
        ai_action_taken="work_order_created",
        points_earned=15,
        impact_points_earned=30,
    )
    assert insight.ai_category == "maintenance_needed"
    assert insight.impact_points_earned == 30


def test_report_schedule():
    sched = ReportSchedule(
        schedule_id="RS-001",
        template_id="TPL-001",
        name="Weekly FM Report",
        query_text="Generate weekly facilities report for Building A",
        frequency="weekly",
        day_of_week=0,
    )
    assert sched.frequency == "weekly"
    assert sched.query_text.startswith("Generate")


def test_budget_utilization():
    budget = Budget(
        budget_id="BUD-001",
        cost_center_id="CC-001",
        fiscal_year=2026,
        category="maintenance",
        allocated_amount=100000.0,
        spent_amount=65000.0,
        committed_amount=15000.0,
    )
    assert budget.remaining == 20000.0
    assert budget.utilization_pct == 65.0
