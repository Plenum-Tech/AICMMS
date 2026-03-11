"""Request/response schemas for documents, reports, and Excel templates API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Document Templates (Story 9) ──────────────────────────────


class DocTemplateCreateRequest(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    template_type: str  # "report", "form", "permission", "approval", "inspection"
    category: str | None = None
    description: str | None = None
    content_schema: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    html_template: str | None = None
    created_by_query: str | None = None


class DocTemplateResponse(BaseModel):
    template_id: str
    name: str
    template_type: str
    category: str | None = None
    description: str | None = None
    content_schema: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_by_query: str | None = None
    created_at: datetime | None = None


# ── Generated Documents ────────────────────────────────────────


class GenerateDocumentRequest(BaseModel):
    template_id: str
    title: str = Field(..., min_length=1, max_length=200)
    content: dict[str, Any] = Field(default_factory=dict)
    related_work_order_id: str | None = None
    related_vendor_id: str | None = None


class GeneratedDocumentResponse(BaseModel):
    document_id: str
    template_id: str | None = None
    title: str
    document_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime | None = None
    generated_by: str | None = None
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    file_url: str | None = None
    related_work_order_id: str | None = None
    related_vendor_id: str | None = None
    created_at: datetime | None = None


# ── Report Schedules (Story 10) ────────────────────────────────


class ReportScheduleCreateRequest(BaseModel):
    schedule_id: str = Field(..., min_length=1, max_length=50)
    template_id: str
    name: str = Field(..., min_length=1, max_length=200)
    query_text: str = Field(..., min_length=1)
    frequency: str  # "daily", "weekly", "monthly"
    day_of_week: int | None = None
    day_of_month: int | None = None
    time_of_day: str | None = None
    recipients: list[str] = Field(default_factory=list)
    delivery_method: str = "in_app"


class ReportScheduleResponse(BaseModel):
    schedule_id: str
    template_id: str
    name: str
    query_text: str
    frequency: str
    is_active: bool = True
    last_generated: datetime | None = None
    next_generation: datetime | None = None
    recipients: list[str] = Field(default_factory=list)
    delivery_method: str
    created_at: datetime | None = None


# ── Excel Templates (Stories 6, 7) ─────────────────────────────


class ExcelTemplateCreateRequest(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    sheet_definitions: list[dict[str, Any]] = Field(default_factory=list)


class ExcelTemplateImportRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    file_url: str
    sheet_definitions: list[dict[str, Any]] = Field(default_factory=list)


class ExcelTemplateResponse(BaseModel):
    template_id: str
    name: str
    description: str | None = None
    source: str  # "imported" or "created"
    original_file_url: str | None = None
    is_integrated: bool = True
    sheet_definitions: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None
