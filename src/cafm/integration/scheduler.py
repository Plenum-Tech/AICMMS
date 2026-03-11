"""Simple cron-like scheduler for pipeline and sync execution."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class ScheduleFrequency(StrEnum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class ScheduledJob:
    """A scheduled job definition."""
    name: str
    frequency: ScheduleFrequency
    callback: Callable[[], Awaitable[Any]]
    interval_minutes: int = 0  # Override for custom intervals
    last_run: datetime | None = None
    next_run: datetime | None = None
    is_active: bool = True
    run_count: int = 0
    error_count: int = 0

    def calculate_next_run(self) -> datetime:
        now = datetime.utcnow()
        intervals = {
            ScheduleFrequency.MINUTELY: timedelta(minutes=1),
            ScheduleFrequency.HOURLY: timedelta(hours=1),
            ScheduleFrequency.DAILY: timedelta(days=1),
            ScheduleFrequency.WEEKLY: timedelta(weeks=1),
            ScheduleFrequency.MONTHLY: timedelta(days=30),
        }
        if self.interval_minutes > 0:
            delta = timedelta(minutes=self.interval_minutes)
        else:
            delta = intervals.get(self.frequency, timedelta(hours=1))
        self.next_run = now + delta
        return self.next_run


class Scheduler:
    """In-process async scheduler for periodic tasks."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def add_job(
        self,
        name: str,
        frequency: ScheduleFrequency,
        callback: Callable[[], Awaitable[Any]],
        interval_minutes: int = 0,
    ) -> ScheduledJob:
        """Register a scheduled job."""
        job = ScheduledJob(
            name=name,
            frequency=frequency,
            callback=callback,
            interval_minutes=interval_minutes,
        )
        job.calculate_next_run()
        self._jobs[name] = job
        logger.info("Scheduled job '%s' (%s), next run: %s", name, frequency, job.next_run)
        return job

    def remove_job(self, name: str) -> None:
        self._jobs.pop(name, None)

    def get_job(self, name: str) -> ScheduledJob | None:
        return self._jobs.get(name)

    def list_jobs(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    async def _run_loop(self) -> None:
        """Main scheduler loop — checks every 30 seconds."""
        while self._running:
            now = datetime.utcnow()
            for job in self._jobs.values():
                if not job.is_active or job.next_run is None:
                    continue
                if now >= job.next_run:
                    try:
                        await job.callback()
                        job.run_count += 1
                        job.last_run = now
                        logger.info("Job '%s' executed (#%d)", job.name, job.run_count)
                    except Exception:
                        job.error_count += 1
                        logger.exception("Job '%s' failed", job.name)
                    job.calculate_next_run()
            await asyncio.sleep(30)

    def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler started with %d jobs", len(self._jobs))

    def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Scheduler stopped")
