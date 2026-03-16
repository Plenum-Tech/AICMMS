"""Request/response schemas for the inspections API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InspectionCreateRequest(BaseModel):
    """Create an inspection report — supports multimodal input."""
    report_id: str = Field(..., min_length=1, max_length=50)
    work_order_id: str | None = None
    schedule_id: str | None = None
    asset_id: str
    building_id: str | None = None
    space_id: str | None = None
    inspection_type: str = "ppm"
    inspector_id: str
    inspection_date: datetime | None = None
    voice_note_urls: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    text_notes: str | None = None
    findings: list[FindingInput] | None = None
    overall_condition: str | None = None


class FindingInput(BaseModel):
    finding_id: str
    category: str
    severity: str = "moderate"
    description: str
    photo_urls: list[str] = Field(default_factory=list)
    location_detail: str | None = None
    recommended_action: str | None = None
    estimated_repair_cost: float | None = None


# Fix forward reference
InspectionCreateRequest.model_rebuild()


class InspectionUpdateRequest(BaseModel):
    status: str | None = None
    text_notes: str | None = None
    voice_note_urls: list[str] | None = None
    photo_urls: list[str] | None = None
    overall_condition: str | None = None
    condition_score: float | None = None


class InspectionResponse(BaseModel):
    report_id: str
    work_order_id: str | None = None
    schedule_id: str | None = None
    asset_id: str
    building_id: str | None = None
    inspection_type: str
    inspector_id: str
    inspection_date: datetime
    status: str
    voice_note_urls: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    text_notes: str | None = None
    transcribed_voice_notes: str | None = None
    overall_condition: str | None = None
    condition_score: float | None = None
    ai_classified_category: str | None = None
    ai_recommended_action: str | None = None
    ai_confidence_score: float | None = None
    follow_up_work_order_id: str | None = None
    requires_immediate_action: bool = False
    points_earned: int = 0
    impact_points_earned: int = 0
    actions_taken: list[str] = Field(default_factory=list)
    prefilled_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class InspectionTemplateResponse(BaseModel):
    template_id: str
    name: str
    asset_category: str | None = None
    inspection_type: str
    checklist_items: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
