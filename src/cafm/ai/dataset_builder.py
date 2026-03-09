"""Build training and inference datasets from CAFM domain data."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class DatasetBuilder:
    """Composes datasets from multiple sources for ML model training.

    Uses the IntegrationManager to fetch domain data and the FeatureStore
    to compute features, then assembles them into tabular datasets.
    """

    def __init__(self, integration_manager: Any, feature_store: Any = None) -> None:
        self._manager = integration_manager
        self._feature_store = feature_store

    async def build_asset_dataset(
        self,
        source_name: str,
        filters: dict[str, Any] | None = None,
        include_features: bool = True,
    ) -> list[dict[str, Any]]:
        """Build a dataset of assets with optional computed features.

        Each row contains asset fields + derived ML features.
        """
        result = await self._manager.query(source_name, "assets", filters=filters, limit=10000)
        rows = result.as_dicts()

        if include_features and self._feature_store:
            enriched = []
            for row in rows:
                asset_id = row.get("asset_id")
                if asset_id:
                    features = await self._feature_store.compute_asset_features(source_name, asset_id)
                    enriched.append({**row, **features})
                else:
                    enriched.append(row)
            return enriched

        return rows

    async def build_work_order_dataset(
        self,
        source_name: str,
        lookback_days: int = 365,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Build a dataset of work orders for routing model training."""
        result = await self._manager.query(source_name, "work_orders", filters=filters, limit=50000)
        return result.as_dicts()

    async def build_occupancy_dataset(
        self,
        source_name: str,
        building_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build an occupancy dataset for space optimization."""
        filters = {"building_id": building_id} if building_id else None
        result = await self._manager.query(source_name, "occupancy_data", filters=filters, limit=100000)
        return result.as_dicts()

    async def build_maintenance_dataset(
        self,
        source_name: str,
        asset_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build a maintenance history dataset for predictive models."""
        filters = {"asset_id": asset_id} if asset_id else None
        result = await self._manager.query(source_name, "maintenance_logs", filters=filters, limit=50000)
        return result.as_dicts()

    async def build_cost_dataset(
        self,
        source_name: str,
        fiscal_year: int | None = None,
    ) -> list[dict[str, Any]]:
        """Build a cost/expense dataset for cost optimization."""
        filters = {"fiscal_year": fiscal_year} if fiscal_year else None
        result = await self._manager.query(source_name, "expenses", filters=filters, limit=50000)
        return result.as_dicts()

    def to_dataframe(self, dataset: list[dict[str, Any]]) -> Any:
        """Convert a dataset to a pandas DataFrame. Requires pandas."""
        import pandas as pd
        return pd.DataFrame(dataset)
