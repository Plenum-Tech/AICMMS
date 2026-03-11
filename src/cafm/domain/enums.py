"""Domain-specific enumerations for CAFM entities."""

from __future__ import annotations

from enum import StrEnum


# ── Asset ─────────────────────────────────────────────────────────


class AssetStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"
    DECOMMISSIONED = "decommissioned"
    DISPOSED = "disposed"


class AssetCondition(StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AssetCriticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Work Order ────────────────────────────────────────────────────


class WorkOrderStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class WorkOrderPriority(StrEnum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkOrderType(StrEnum):
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    PREDICTIVE = "predictive"
    INSPECTION = "inspection"
    EMERGENCY = "emergency"
    RENOVATION = "renovation"


# ── Maintenance ───────────────────────────────────────────────────


class MaintenanceFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class FailureSeverity(StrEnum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


# ── Facility / Space ──────────────────────────────────────────────


class SpaceType(StrEnum):
    OFFICE = "office"
    MEETING_ROOM = "meeting_room"
    COMMON_AREA = "common_area"
    RESTROOM = "restroom"
    KITCHEN = "kitchen"
    STORAGE = "storage"
    SERVER_ROOM = "server_room"
    MECHANICAL = "mechanical"
    PARKING = "parking"
    LOBBY = "lobby"
    HALLWAY = "hallway"
    STAIRWELL = "stairwell"
    ELEVATOR = "elevator"
    OTHER = "other"


class BuildingStatus(StrEnum):
    OPERATIONAL = "operational"
    UNDER_CONSTRUCTION = "under_construction"
    RENOVATION = "renovation"
    CLOSED = "closed"
    DEMOLISHED = "demolished"


# ── Vendor / Contract ─────────────────────────────────────────────


class ContractStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class VendorType(StrEnum):
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    SECURITY = "security"
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    LANDSCAPING = "landscaping"
    IT_SERVICES = "it_services"
    GENERAL = "general"


# ── Sensor / IoT ──────────────────────────────────────────────────


class SensorType(StrEnum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    OCCUPANCY = "occupancy"
    ENERGY = "energy"
    WATER = "water"
    AIR_QUALITY = "air_quality"
    NOISE = "noise"
    LIGHT = "light"
    VIBRATION = "vibration"
    PRESSURE = "pressure"


class DeviceStatus(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"
