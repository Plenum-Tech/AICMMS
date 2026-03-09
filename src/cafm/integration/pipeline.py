"""ETL pipeline definition and execution engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from cafm.connectors.base import Connector
from cafm.core.events import Event, EventBus, EventType
from cafm.core.exceptions import PipelineError
from cafm.core.types import RawRow
from cafm.integration.transforms import TransformFn, chain_transforms

logger = logging.getLogger(__name__)


class PipelineStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStep:
    """A single step in a pipeline."""
    name: str
    step_type: str  # "extract", "transform", "load"
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    pipeline_name: str
    status: PipelineStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class Pipeline:
    """An Extract-Transform-Load pipeline definition.

    Usage::

        pipeline = Pipeline("sync_assets")
        pipeline.extract("legacy_db", "equipment")
        pipeline.transform(rename_fields({"equip_id": "asset_id"}))
        pipeline.transform(cast_fields({"cost": "float"}))
        pipeline.load("main_db", "assets")
    """

    def __init__(self, name: str, event_bus: EventBus | None = None) -> None:
        self.name = name
        self._event_bus = event_bus or EventBus()
        self._source_name: str | None = None
        self._source_table: str | None = None
        self._target_name: str | None = None
        self._target_table: str | None = None
        self._transforms: list[TransformFn] = []
        self._extract_filters: dict[str, Any] | None = None
        self._extract_limit: int | None = None

    def extract(
        self,
        source_name: str,
        table: str,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> Pipeline:
        """Define the extraction source."""
        self._source_name = source_name
        self._source_table = table
        self._extract_filters = filters
        self._extract_limit = limit
        return self

    def transform(self, transform_fn: TransformFn) -> Pipeline:
        """Add a transform step."""
        self._transforms.append(transform_fn)
        return self

    def load(self, target_name: str, table: str) -> Pipeline:
        """Define the load target."""
        self._target_name = target_name
        self._target_table = table
        return self

    async def execute(
        self,
        connectors: dict[str, Connector],
    ) -> PipelineResult:
        """Execute the pipeline using provided connectors.

        Args:
            connectors: Map of source_name -> connected Connector instances.
        """
        result = PipelineResult(
            pipeline_name=self.name,
            status=PipelineStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        await self._event_bus.publish(Event(
            type=EventType.PIPELINE_STARTED,
            source=self.name,
        ))

        try:
            # Extract
            if not self._source_name or not self._source_table:
                raise PipelineError("No extract source defined")
            source = connectors.get(self._source_name)
            if source is None:
                raise PipelineError(f"Source connector '{self._source_name}' not found")

            rows = await source.fetch_rows(
                self._source_table,
                filters=self._extract_filters,
                limit=self._extract_limit,
            )
            result.rows_extracted = len(rows)
            logger.info("Pipeline %s: extracted %d rows from %s.%s",
                        self.name, len(rows), self._source_name, self._source_table)

            # Transform
            if self._transforms:
                combined = chain_transforms(*self._transforms)
                rows = combined(rows)
            result.rows_transformed = len(rows)

            # Load
            if self._target_name and self._target_table and rows:
                target = connectors.get(self._target_name)
                if target is None:
                    raise PipelineError(f"Target connector '{self._target_name}' not found")
                await target.insert_rows(self._target_table, rows)
                result.rows_loaded = len(rows)
                logger.info("Pipeline %s: loaded %d rows into %s.%s",
                            self.name, len(rows), self._target_name, self._target_table)

            result.status = PipelineStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - result.started_at).total_seconds()

            await self._event_bus.publish(Event(
                type=EventType.PIPELINE_COMPLETED,
                source=self.name,
                payload={"rows_loaded": result.rows_loaded},
            ))

        except Exception as exc:
            result.status = PipelineStatus.FAILED
            result.completed_at = datetime.utcnow()
            result.errors.append(str(exc))
            await self._event_bus.publish(Event(
                type=EventType.PIPELINE_FAILED,
                source=self.name,
                payload={"error": str(exc)},
            ))
            raise PipelineError(f"Pipeline '{self.name}' failed: {exc}") from exc

        return result
