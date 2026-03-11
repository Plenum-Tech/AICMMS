"""Request/response schemas for the vendors & contracts API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from cafm.domain.enums import ContractStatus, VendorType


class VendorCreateRequest(BaseModel):
    vendor_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    vendor_type: VendorType = VendorType.GENERAL
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    specializations: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class VendorUpdateRequest(BaseModel):
    name: str | None = None
    vendor_type: VendorType | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    rating: float | None = None
    specializations: list[str] | None = None


class VendorResponse(BaseModel):
    vendor_id: str
    name: str
    vendor_type: VendorType
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    is_active: bool = True
    rating: float | None = None
    specializations: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class ContractCreateRequest(BaseModel):
    contract_id: str = Field(..., min_length=1, max_length=50)
    vendor_id: str
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    contract_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    total_value: float | None = None
    monthly_value: float | None = None
    auto_renewal: bool = False
    terms: str | None = None


class ContractResponse(BaseModel):
    contract_id: str
    vendor_id: str
    title: str
    description: str | None = None
    status: ContractStatus
    contract_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    total_value: float | None = None
    monthly_value: float | None = None
    auto_renewal: bool = False
    created_at: datetime | None = None


class SLACreateRequest(BaseModel):
    sla_id: str = Field(..., min_length=1, max_length=50)
    contract_id: str
    metric_name: str
    target_value: float
    unit: str
    measurement_period: str | None = None
    penalty_clause: str | None = None


class SLAResponse(BaseModel):
    sla_id: str
    contract_id: str
    metric_name: str
    target_value: float
    unit: str
    measurement_period: str | None = None
    penalty_clause: str | None = None
