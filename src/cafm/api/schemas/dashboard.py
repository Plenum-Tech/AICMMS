"""Request/response schemas for the command center / dashboard API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    """High-level dashboard metrics (Command Center)."""

    # Asset metrics
    total_assets: int = 0
    active_assets: int = 0
    critical_assets: int = 0
    assets_under_maintenance: int = 0

    # Work order metrics
    open_work_orders: int = 0
    overdue_work_orders: int = 0
    completed_this_month: int = 0
    avg_resolution_hours: float | None = None

    # Maintenance metrics
    upcoming_ppm_count: int = 0
    ppm_compliance_pct: float | None = None  # % completed on time
    sla_compliance_pct: float | None = None

    # Cost metrics
    total_spend_mtd: float | None = None
    budget_utilization_pct: float | None = None

    # Technician metrics
    total_technicians: int = 0
    available_technicians: int = 0
    avg_technician_satisfaction: float | None = None

    generated_at: datetime = Field(default_factory=lambda: datetime.now())


class MetricTimeSeries(BaseModel):
    """Time-series metric data point."""

    timestamp: datetime
    value: float
    label: str | None = None


class DashboardWidget(BaseModel):
    """Configurable dashboard widget definition."""

    widget_id: str
    widget_type: str  # "kpi", "chart", "table", "map"
    title: str
    metric_key: str
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, int] = Field(default_factory=dict)  # {x, y, w, h}


class SLAMetric(BaseModel):
    """SLA tracking metric."""

    sla_name: str
    target_value: float
    actual_value: float
    compliance_pct: float
    breaches_count: int = 0
    period: str  # "daily", "weekly", "monthly"


class AlertResponse(BaseModel):
    """Real-time alert for the command center."""

    alert_id: str
    severity: str  # "info", "warning", "critical"
    category: str  # "asset", "work_order", "sla", "cost", "sensor"
    title: str
    message: str
    source_id: str | None = None  # e.g., asset_id, work_order_id
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    acknowledged: bool = False
