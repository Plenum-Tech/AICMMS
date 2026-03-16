"""Document and form template domain models.

Supports the AICMMS spec requirements for:
- Query-to-create document templates
- Site permissions, vendor approval forms
- Auto-generated FM reports (daily/weekly/monthly)
- Saved periodic auto-query report templates
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class DocumentTemplate(CAFMBaseModel):
    """Reusable document or form template."""

    template_id: str
    name: str
    template_type: str  # "report", "form", "permission", "approval", "inspection"
    category: str | None = None  # e.g., "site_permission", "vendor_approval", "monthly_report"
    description: str | None = None
    content_schema: dict[str, Any] = Field(default_factory=dict)  # JSON schema for fields
    default_values: dict[str, Any] = Field(default_factory=dict)
    html_template: str | None = None
    is_active: bool = True
    created_by_query: str | None = None  # The original query that created this template


class GeneratedDocument(CAFMBaseModel):
    """An instance of a generated document from a template."""

    document_id: str
    template_id: str | None = None
    title: str
    document_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime | None = None
    generated_by: str | None = None
    status: str = "draft"  # draft, pending_approval, approved, rejected, archived
    approved_by: str | None = None
    approved_at: datetime | None = None
    file_url: str | None = None
    related_work_order_id: str | None = None
    related_vendor_id: str | None = None
    related_asset_id: str | None = None
    notes: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class ReportSchedule(CAFMBaseModel):
    """Scheduled auto-generated report (periodic auto-query).

    When a facilities manager queries a report for the first time,
    they can save it as a template with a schedule so it auto-generates.
    """

    schedule_id: str
    template_id: str
    name: str
    query_text: str  # The original query that generates this report
    frequency: str  # "daily", "weekly", "monthly"
    day_of_week: int | None = None  # 0=Monday, for weekly
    day_of_month: int | None = None  # For monthly
    time_of_day: str | None = None  # e.g., "08:00"
    recipients: list[str] = Field(default_factory=list)  # email or user_ids
    delivery_method: str = "in_app"  # "in_app", "email", "both"
    is_active: bool = True
    last_generated: datetime | None = None
    next_generation: datetime | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class ExcelTemplate(CAFMBaseModel):
    """Excel-like template that can be maintained within the platform.

    Supports the spec requirement for Excel UI interface where FM managers
    maintain additional templates integrated with the platform.
    """

    template_id: str
    name: str
    description: str | None = None
    sheet_definitions: list[SheetDefinition] = Field(default_factory=list)
    source: str = "created"  # "imported" or "created"
    original_file_url: str | None = None
    is_integrated: bool = True  # Data available for insights
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class SheetDefinition(CAFMBaseModel):
    """Definition of a single sheet within an Excel template."""

    sheet_name: str
    column_definitions: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int | None = None
    is_primary: bool = False
    linked_domain: str | None = None  # e.g., "assets", "work_orders" for integration
