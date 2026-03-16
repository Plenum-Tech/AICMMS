"""Abstract data provider contracts for AI consumers.

Each AI capability (predictive maintenance, space optimization, work order
routing, cost optimization) defines a data contract interface here.  The
integration layer provides concrete implementations that fetch data from
connected sources via the IntegrationManager.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PredictiveMaintenanceDataProvider(ABC):
    """Data contract for predictive maintenance models."""

    @abstractmethod
    async def get_asset_history(
        self, asset_id: str, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Get maintenance history for an asset."""
        ...

    @abstractmethod
    async def get_failure_events(
        self, asset_id: str | None = None, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Get failure events, optionally filtered by asset."""
        ...

    @abstractmethod
    async def get_sensor_readings(
        self, asset_id: str, metric: str, lookback_days: int = 30
    ) -> list[dict[str, Any]]:
        """Get sensor readings for an asset and metric type."""
        ...

    @abstractmethod
    async def get_asset_features(self, asset_id: str) -> dict[str, Any]:
        """Get computed features for a single asset (MTBF, age, failure count, etc.)."""
        ...


class SpaceOptimizationDataProvider(ABC):
    """Data contract for space optimization models."""

    @abstractmethod
    async def get_occupancy_timeseries(
        self, space_id: str, lookback_days: int = 90
    ) -> list[dict[str, Any]]:
        """Get occupancy time-series data for a space."""
        ...

    @abstractmethod
    async def get_space_inventory(
        self, building_id: str
    ) -> list[dict[str, Any]]:
        """Get all spaces in a building with utilization metrics."""
        ...

    @abstractmethod
    async def get_reservation_patterns(
        self, space_id: str, lookback_days: int = 90
    ) -> list[dict[str, Any]]:
        """Get booking/reservation patterns for a space."""
        ...


class WorkOrderRoutingDataProvider(ABC):
    """Data contract for intelligent work order routing."""

    @abstractmethod
    async def get_historical_assignments(
        self, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Get historical WO assignments with outcomes."""
        ...

    @abstractmethod
    async def get_technician_profiles(self) -> list[dict[str, Any]]:
        """Get all technicians with skills, availability, workload."""
        ...

    @abstractmethod
    async def get_pending_work_orders(self) -> list[dict[str, Any]]:
        """Get unassigned work orders awaiting routing."""
        ...


class CostOptimizationDataProvider(ABC):
    """Data contract for cost optimization models."""

    @abstractmethod
    async def get_expense_history(
        self, cost_center_id: str | None = None, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Get expense history optionally filtered by cost center."""
        ...

    @abstractmethod
    async def get_asset_cost_metrics(
        self, asset_id: str
    ) -> dict[str, Any]:
        """Get cost metrics for an asset (repair vs replace ratio, TCO, etc.)."""
        ...

    @abstractmethod
    async def get_vendor_cost_comparison(
        self, service_type: str
    ) -> list[dict[str, Any]]:
        """Compare vendor costs for a service type."""
        ...

    @abstractmethod
    async def get_budget_utilization(
        self, fiscal_year: int
    ) -> list[dict[str, Any]]:
        """Get budget utilization across cost centers."""
        ...


class InspectionAIDataProvider(ABC):
    """Data contract for AI-powered inspection classification.

    Per AICMMS spec: voice notes and images from inspections get
    classified, and appropriate actions are triggered automatically.
    """

    @abstractmethod
    async def get_inspection_history(
        self, asset_id: str, lookback_days: int = 365
    ) -> list[dict[str, Any]]:
        """Get inspection history for an asset."""
        ...

    @abstractmethod
    async def get_asset_insights(
        self, asset_id: str
    ) -> list[dict[str, Any]]:
        """Get technician-submitted insights for an asset."""
        ...

    @abstractmethod
    async def get_failure_modes(
        self, asset_category: str
    ) -> list[dict[str, Any]]:
        """Get known failure modes for an asset category."""
        ...
