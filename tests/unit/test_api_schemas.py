"""Tests for API request/response schemas."""

from __future__ import annotations

import pytest

from cafm.api.schemas.common import (
    APIResponse,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
)
from cafm.api.schemas.connectors import (
    ConnectorCreateRequest,
    ConnectorTestResult,
    QueryRequest,
)
from cafm.api.schemas.assets import AssetCreateRequest, AssetResponse
from cafm.api.schemas.work_orders import (
    WorkOrderAdHocRequest,
    WorkOrderCreateRequest,
)
from cafm.api.schemas.technicians import TechnicianCreateRequest
from cafm.api.schemas.dashboard import DashboardSummary, AlertResponse
from cafm.core.types import DataSourceType
from cafm.domain.enums import AssetCondition, AssetStatus, WorkOrderPriority


class TestCommonSchemas:
    """Tests for shared response schemas."""

    def test_api_response(self):
        resp = APIResponse(data={"key": "value"}, message="ok")
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.message == "ok"
        assert resp.timestamp is not None

    def test_error_response(self):
        resp = ErrorResponse(error="NotFound", detail="Item not found")
        assert resp.success is False
        assert resp.error == "NotFound"

    def test_paginated_response(self):
        items = [{"id": i} for i in range(10)]
        resp = PaginatedResponse.create(items=items, total=45, page=2, page_size=10)
        assert resp.total == 45
        assert resp.page == 2
        assert resp.total_pages == 5
        assert resp.has_next is True
        assert resp.has_previous is True
        assert len(resp.items) == 10

    def test_paginated_response_first_page(self):
        resp = PaginatedResponse.create(items=[], total=20, page=1, page_size=10)
        assert resp.has_previous is False
        assert resp.has_next is True

    def test_paginated_response_last_page(self):
        resp = PaginatedResponse.create(items=[], total=20, page=2, page_size=10)
        assert resp.has_next is False
        assert resp.has_previous is True

    def test_health_response(self):
        resp = HealthResponse(
            status="healthy",
            active_connectors=3,
            components={"db": "ok", "cache": "ok"},
        )
        assert resp.status == "healthy"
        assert resp.active_connectors == 3


class TestConnectorSchemas:
    """Tests for connector request/response schemas."""

    def test_connector_create_request(self):
        req = ConnectorCreateRequest(
            name="test_db",
            source_type=DataSourceType.POSTGRESQL,
            connection_params={"url": "postgresql://localhost/test"},
        )
        assert req.name == "test_db"
        assert req.source_type == DataSourceType.POSTGRESQL

    def test_connector_create_validation(self):
        with pytest.raises(Exception):  # Pydantic validation
            ConnectorCreateRequest(
                name="",  # too short
                source_type=DataSourceType.POSTGRESQL,
                connection_params={},
            )

    def test_query_request(self):
        req = QueryRequest(
            source_name="db1", table="assets",
            filters={"status": "active"}, limit=50,
        )
        assert req.limit == 50
        assert req.offset == 0

    def test_connector_test_result(self):
        result = ConnectorTestResult(name="db1", healthy=True, latency_ms=12.5)
        assert result.healthy is True
        assert result.error is None


class TestAssetSchemas:
    """Tests for asset schemas."""

    def test_asset_create_request(self):
        req = AssetCreateRequest(
            asset_id="AST-001",
            name="HVAC Unit",
            category="hvac",
            facility_id="BLD-001",
            status=AssetStatus.ACTIVE,
            condition=AssetCondition.GOOD,
        )
        assert req.asset_id == "AST-001"
        assert req.onboarding_method == "manual"

    def test_asset_response_model(self):
        resp = AssetResponse(
            asset_id="AST-001",
            name="HVAC Unit",
            category="hvac",
            facility_id="BLD-001",
            status=AssetStatus.ACTIVE,
            condition=AssetCondition.GOOD,
            criticality="medium",
            qr_code="AICMMS-AST-001-ABC12345",
        )
        assert resp.qr_code is not None
        assert resp.failure_count == 0


class TestWorkOrderSchemas:
    """Tests for work order schemas."""

    def test_work_order_create_request(self):
        req = WorkOrderCreateRequest(
            work_order_id="WO-001",
            title="Fix broken AC",
            priority=WorkOrderPriority.HIGH,
        )
        assert req.work_order_id == "WO-001"

    def test_adhoc_work_order_request(self):
        req = WorkOrderAdHocRequest(
            text="The AC unit in room 302 is making a loud noise",
            building_id="BLD-001",
            priority=WorkOrderPriority.MEDIUM,
        )
        assert len(req.text) > 0


class TestTechnicianSchemas:
    """Tests for technician schemas."""

    def test_technician_create_request(self):
        req = TechnicianCreateRequest(
            technician_id="TECH-001",
            first_name="John",
            last_name="Doe",
            skill_codes=["hvac", "electrical"],
        )
        assert len(req.skill_codes) == 2


class TestDashboardSchemas:
    """Tests for dashboard schemas."""

    def test_dashboard_summary(self):
        summary = DashboardSummary(
            total_assets=500,
            active_assets=450,
            open_work_orders=25,
        )
        assert summary.total_assets == 500
        assert summary.critical_assets == 0  # default

    def test_alert_response(self):
        alert = AlertResponse(
            alert_id="alert-001",
            severity="critical",
            category="asset",
            title="Critical Asset",
            message="HVAC unit in critical condition",
        )
        assert alert.acknowledged is False
