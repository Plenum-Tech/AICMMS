"""Vendor and contract domain models."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import Field

from cafm.domain.enums import ContractStatus, VendorType
from cafm.models.base import CAFMBaseModel


class Vendor(CAFMBaseModel):
    """Service provider / vendor."""

    vendor_id: str
    name: str
    vendor_type: VendorType = VendorType.GENERAL
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    is_active: bool = True
    rating: float | None = None  # 1-5 scale
    specializations: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Contract(CAFMBaseModel):
    """Service contract with a vendor."""

    contract_id: str
    vendor_id: str
    title: str
    description: str | None = None
    status: ContractStatus = ContractStatus.ACTIVE
    contract_type: str | None = None  # e.g., "fixed_price", "time_and_materials"
    start_date: date | None = None
    end_date: date | None = None
    total_value: float | None = None
    monthly_value: float | None = None
    auto_renewal: bool = False
    renewal_notice_days: int | None = None
    terms: str | None = None
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class ServiceLevel(CAFMBaseModel):
    """SLA definition within a contract."""

    sla_id: str
    contract_id: str
    metric_name: str  # e.g., "response_time_hours", "resolution_time_hours"
    target_value: float
    unit: str  # e.g., "hours", "percent", "minutes"
    measurement_period: str | None = None  # e.g., "monthly", "quarterly"
    penalty_clause: str | None = None
    description: str | None = None
