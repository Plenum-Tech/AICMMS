"""Service layer for documents, reports, and Excel templates (Stories 6,7,9,10)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cafm.core.events import Event, EventBus, EventType
from cafm.domain.documents import (
    DocumentTemplate,
    ExcelTemplate,
    GeneratedDocument,
    ReportSchedule,
)
from cafm.repository.base import Repository

logger = logging.getLogger(__name__)


class DocumentService:
    """Business logic for document templates, generated documents, and reports.

    Stories 9, 10: query-to-create templates, auto-generate periodic reports.
    """

    def __init__(
        self,
        template_repo: Repository[DocumentTemplate],
        document_repo: Repository[GeneratedDocument],
        schedule_repo: Repository[ReportSchedule],
        event_bus: EventBus,
    ) -> None:
        self._template_repo = template_repo
        self._document_repo = document_repo
        self._schedule_repo = schedule_repo
        self._event_bus = event_bus

    # ── Templates ──────────────────────────────────────────────

    async def create_template(
        self, data: dict[str, Any], created_by: str | None = None,
    ) -> DocumentTemplate:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        template = DocumentTemplate(**data)
        return await self._template_repo.create(template)

    async def get_template(self, template_id: str) -> DocumentTemplate | None:
        return await self._template_repo.get_by_id(template_id)

    async def list_templates(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[DocumentTemplate], int]:
        result = await self._template_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._template_repo.count(filters=filters)
        templates = [DocumentTemplate(**r.data) for r in result.records]
        return templates, total

    async def update_template(
        self, template_id: str, updates: dict[str, Any],
    ) -> DocumentTemplate | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._template_repo.update(template_id, updates)

    # ── Generated Documents ────────────────────────────────────

    async def generate_document(
        self,
        template_id: str,
        content: dict[str, Any],
        title: str,
        generated_by: str | None = None,
        related_work_order_id: str | None = None,
        related_vendor_id: str | None = None,
    ) -> GeneratedDocument:
        """Generate a document from a template (Story 9)."""
        template = await self._template_repo.get_by_id(template_id)
        doc = GeneratedDocument(
            document_id=f"DOC-{uuid.uuid4().hex[:8].upper()}",
            template_id=template_id,
            title=title,
            document_type=template.template_type if template else "general",
            content=content,
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            status="draft",
            related_work_order_id=related_work_order_id,
            related_vendor_id=related_vendor_id,
        )
        created = await self._document_repo.create(doc)
        await self._event_bus.publish(Event(
            type=EventType.RECORD_CREATED, source="document_service",
            payload={"entity": "document", "document_id": created.document_id},
        ))
        return created

    async def get_document(self, document_id: str) -> GeneratedDocument | None:
        return await self._document_repo.get_by_id(document_id)

    async def list_documents(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[GeneratedDocument], int]:
        result = await self._document_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._document_repo.count(filters=filters)
        docs = [GeneratedDocument(**r.data) for r in result.records]
        return docs, total

    async def approve_document(
        self, document_id: str, approved_by: str,
    ) -> GeneratedDocument | None:
        return await self._document_repo.update(document_id, {
            "status": "approved",
            "approved_by": approved_by,
            "approved_at": datetime.utcnow(),
        })

    # ── Report Schedules (Story 10) ────────────────────────────

    async def create_report_schedule(
        self, data: dict[str, Any],
    ) -> ReportSchedule:
        data["created_at"] = datetime.utcnow()
        schedule = ReportSchedule(**data)
        return await self._schedule_repo.create(schedule)

    async def get_schedule(self, schedule_id: str) -> ReportSchedule | None:
        return await self._schedule_repo.get_by_id(schedule_id)

    async def list_schedules(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[ReportSchedule], int]:
        result = await self._schedule_repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._schedule_repo.count(filters=filters)
        schedules = [ReportSchedule(**r.data) for r in result.records]
        return schedules, total

    async def get_active_schedules(self) -> list[ReportSchedule]:
        schedules, _ = await self.list_schedules(filters={"is_active": True}, limit=500)
        return schedules


class ExcelTemplateService:
    """Business logic for Excel templates (Stories 6, 7)."""

    def __init__(
        self,
        template_repo: Repository[ExcelTemplate],
        event_bus: EventBus,
    ) -> None:
        self._repo = template_repo
        self._event_bus = event_bus

    async def create_template(
        self, data: dict[str, Any], created_by: str | None = None,
    ) -> ExcelTemplate:
        data["created_at"] = datetime.utcnow()
        data["created_by"] = created_by
        template = ExcelTemplate(**data)
        return await self._repo.create(template)

    async def import_template(
        self,
        name: str,
        file_url: str,
        sheet_definitions: list[dict[str, Any]],
    ) -> ExcelTemplate:
        """Import an existing Excel template (Story 7)."""
        template = ExcelTemplate(
            template_id=f"XLS-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            source="imported",
            original_file_url=file_url,
            sheet_definitions=sheet_definitions,
            is_integrated=True,
        )
        template.created_at = datetime.utcnow()
        return await self._repo.create(template)

    async def get_template(self, template_id: str) -> ExcelTemplate | None:
        return await self._repo.get_by_id(template_id)

    async def list_templates(
        self, filters: dict[str, Any] | None = None, limit: int = 50, offset: int = 0,
    ) -> tuple[list[ExcelTemplate], int]:
        result = await self._repo.get_all(filters=filters, limit=limit, offset=offset)
        total = await self._repo.count(filters=filters)
        templates = [ExcelTemplate(**r.data) for r in result.records]
        return templates, total

    async def update_template(
        self, template_id: str, updates: dict[str, Any],
    ) -> ExcelTemplate | None:
        updates["updated_at"] = datetime.utcnow()
        updates = {k: v for k, v in updates.items() if v is not None}
        return await self._repo.update(template_id, updates)
