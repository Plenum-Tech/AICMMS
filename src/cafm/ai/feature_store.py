"""Feature extraction and storage for ML model training.

Extracts domain-specific features from CAFM data for predictive
maintenance, space optimization and cost optimization models.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class FeatureStore:
    """Extracts and caches ML features from CAFM domain data.

    Works with the IntegrationManager to fetch raw data and compute
    derived features suitable for model training and inference.
    """

    def __init__(self, integration_manager: Any) -> None:
        self._manager = integration_manager
        self._cache: dict[str, dict[str, Any]] = {}

    async def compute_asset_features(
        self, source_name: str, asset_id: str
    ) -> dict[str, Any]:
        """Compute predictive maintenance features for a single asset."""
        # Fetch asset record
        result = await self._manager.query(
            source_name, "assets", filters={"asset_id": asset_id}, limit=1
        )
        if result.is_empty:
            return {}

        asset = result.as_dicts()[0]

        # Compute derived features
        features: dict[str, Any] = {
            "asset_id": asset_id,
            "asset_age_days": self._compute_age_days(asset.get("installation_date")),
            "failure_count": asset.get("failure_count", 0),
            "mtbf_hours": asset.get("mean_time_between_failures"),
            "total_downtime_hours": asset.get("total_downtime_hours", 0),
            "condition": asset.get("condition"),
            "criticality": asset.get("criticality"),
        }

        # Financial features
        purchase_cost = asset.get("purchase_cost", 0) or 0
        replacement_cost = asset.get("replacement_cost", 0) or 0
        if replacement_cost > 0:
            features["repair_replace_ratio"] = purchase_cost / replacement_cost
        else:
            features["repair_replace_ratio"] = None

        # Age ratio (current age / expected life)
        if asset.get("expected_end_of_life") and asset.get("installation_date"):
            try:
                install = datetime.fromisoformat(str(asset["installation_date"]))
                eol = datetime.fromisoformat(str(asset["expected_end_of_life"]))
                expected_life_days = (eol - install).days
                age_days = features["asset_age_days"] or 0
                features["life_ratio"] = age_days / expected_life_days if expected_life_days > 0 else None
            except (ValueError, TypeError):
                features["life_ratio"] = None
        else:
            features["life_ratio"] = None

        # Warranty status
        warranty = asset.get("warranty_expiry")
        if warranty:
            try:
                expiry = datetime.fromisoformat(str(warranty))
                features["warranty_remaining_days"] = (expiry - datetime.utcnow()).days
                features["under_warranty"] = features["warranty_remaining_days"] > 0
            except (ValueError, TypeError):
                features["warranty_remaining_days"] = None
                features["under_warranty"] = None
        else:
            features["warranty_remaining_days"] = None
            features["under_warranty"] = None

        cache_key = f"{source_name}:{asset_id}"
        self._cache[cache_key] = features
        return features

    async def compute_space_features(
        self, source_name: str, space_id: str
    ) -> dict[str, Any]:
        """Compute space utilization features."""
        result = await self._manager.query(
            source_name, "spaces", filters={"space_id": space_id}, limit=1
        )
        if result.is_empty:
            return {}

        space = result.as_dicts()[0]

        return {
            "space_id": space_id,
            "area_sqft": space.get("area_sqft"),
            "capacity": space.get("capacity"),
            "space_type": space.get("space_type"),
            "is_bookable": space.get("is_bookable"),
            "department": space.get("department"),
        }

    def get_cached(self, key: str) -> dict[str, Any] | None:
        return self._cache.get(key)

    def clear_cache(self) -> None:
        self._cache.clear()

    @staticmethod
    def _compute_age_days(date_str: Any) -> int | None:
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(str(date_str))
            return (datetime.utcnow() - dt).days
        except (ValueError, TypeError):
            return None
