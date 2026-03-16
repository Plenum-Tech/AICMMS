"""Inspection report domain models.

Supports the multimodal inspection workflow: technicians record
findings via voice notes, photos and text on mobile, and the platform
auto-populates structured inspection reports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from cafm.models.base import CAFMBaseModel


class InspectionReport(CAFMBaseModel):
    """Structured inspection report for a PPM or ad-hoc work order."""

    report_id: str
    work_order_id: str | None = None
    schedule_id: str | None = None  # If part of a PM schedule
    asset_id: str
    building_id: str | None = None
    space_id: str | None = None

    # Inspection details
    inspection_type: str  # "ppm", "adhoc", "condition_assessment", "safety"
    inspector_id: str  # technician_id
    inspection_date: datetime
    status: str = "draft"  # draft, submitted, reviewed, approved, rejected

    # Multimodal inputs
    voice_note_urls: list[str] = Field(default_factory=list)
    photo_urls: list[str] = Field(default_factory=list)
    text_notes: str | None = None
    transcribed_voice_notes: str | None = None  # AI-transcribed from voice

    # Structured findings
    findings: list[InspectionFinding] = Field(default_factory=list)
    overall_condition: str | None = None  # excellent, good, fair, poor, critical
    condition_score: float | None = None  # 0-100

    # Pre-filled config data (spec says ~50% pre-filled)
    prefilled_data: dict[str, Any] = Field(default_factory=dict)

    # Actions triggered
    actions_taken: list[str] = Field(default_factory=list)
    follow_up_work_order_id: str | None = None
    requires_immediate_action: bool = False

    # AI classification
    ai_classified_category: str | None = None
    ai_recommended_action: str | None = None
    ai_confidence_score: float | None = None

    # Gamification
    points_earned: int = 0
    impact_points_earned: int = 0

    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class InspectionFinding(CAFMBaseModel):
    """Individual finding within an inspection report."""

    finding_id: str
    report_id: str
    category: str  # e.g., "safety", "wear", "damage", "leak", "noise"
    severity: str = "moderate"  # minor, moderate, major, critical
    description: str
    photo_urls: list[str] = Field(default_factory=list)
    location_detail: str | None = None
    recommended_action: str | None = None
    estimated_repair_cost: float | None = None
    is_resolved: bool = False
    resolved_date: datetime | None = None


class InspectionTemplate(CAFMBaseModel):
    """Reusable inspection template with pre-configured checklist items."""

    template_id: str
    name: str
    asset_category: str | None = None
    inspection_type: str
    checklist_items: list[ChecklistItem] = Field(default_factory=list)
    description: str | None = None
    is_active: bool = True


class ChecklistItem(CAFMBaseModel):
    """A single checklist item in an inspection template."""

    item_id: str
    sequence: int
    category: str
    description: str
    expected_values: list[str] = Field(default_factory=list)  # e.g., ["pass", "fail", "na"]
    is_required: bool = True
    measurement_unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
