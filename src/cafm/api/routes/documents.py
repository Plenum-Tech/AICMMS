"""Document templates, generated documents, report schedules, and Excel templates API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.documents import (
    DocTemplateCreateRequest, DocTemplateResponse,
    ExcelTemplateCreateRequest, ExcelTemplateImportRequest, ExcelTemplateResponse,
    GenerateDocumentRequest, GeneratedDocumentResponse,
    ReportScheduleCreateRequest, ReportScheduleResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents & Reports"])

_document_service = None
_excel_service = None


def get_document_service():
    if _document_service is None:
        raise HTTPException(status_code=503, detail="Document service not initialized")
    return _document_service


def set_document_service(svc) -> None:
    global _document_service
    _document_service = svc


def get_excel_service():
    if _excel_service is None:
        raise HTTPException(status_code=503, detail="Excel template service not initialized")
    return _excel_service


def set_excel_service(svc) -> None:
    global _excel_service
    _excel_service = svc


# ── Document Templates (Story 9) ─────────────────────────────


@router.get("/templates", response_model=PaginatedResponse[DocTemplateResponse])
async def list_templates(
    pagination: Pagination, user: CurrentUser,
    template_type: str | None = Query(None), category: str | None = Query(None),
    svc=Depends(get_document_service),
):
    filters = {}
    if template_type: filters["template_type"] = template_type
    if category: filters["category"] = category
    templates, total = await svc.list_templates(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [DocTemplateResponse(**t.model_dump()) for t in templates]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/templates", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: DocTemplateCreateRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_document_service),
):
    """Create a document template (Story 9: query-to-create)."""
    template = await svc.create_template(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=DocTemplateResponse(**template.model_dump()), message=f"Template '{template.template_id}' created")


@router.get("/templates/{template_id}", response_model=APIResponse)
async def get_template(template_id: str, user: CurrentUser, svc=Depends(get_document_service)):
    template = await svc.get_template(template_id)
    if not template: raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return APIResponse(data=DocTemplateResponse(**template.model_dump()))


@router.patch("/templates/{template_id}", response_model=APIResponse)
async def update_template(
    template_id: str, request: DocTemplateCreateRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_document_service),
):
    updated = await svc.update_template(template_id, request.model_dump(exclude_unset=True))
    if not updated: raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return APIResponse(data=DocTemplateResponse(**updated.model_dump()))


# ── Generated Documents ───────────────────────────────────────


@router.post("/generate", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def generate_document(
    request: GenerateDocumentRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_document_service),
):
    """Generate a document from a template (Story 9)."""
    doc = await svc.generate_document(
        template_id=request.template_id, content=request.content, title=request.title,
        generated_by=user.user_id, related_work_order_id=request.related_work_order_id,
        related_vendor_id=request.related_vendor_id,
    )
    return APIResponse(data=GeneratedDocumentResponse(**doc.model_dump()), message="Document generated")


@router.get("/generated", response_model=PaginatedResponse[GeneratedDocumentResponse])
async def list_documents(
    pagination: Pagination, user: CurrentUser,
    document_type: str | None = Query(None), status_filter: str | None = Query(None, alias="status"),
    svc=Depends(get_document_service),
):
    filters = {}
    if document_type: filters["document_type"] = document_type
    if status_filter: filters["status"] = status_filter
    docs, total = await svc.list_documents(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [GeneratedDocumentResponse(**d.model_dump()) for d in docs]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/generated/{document_id}", response_model=APIResponse)
async def get_document(document_id: str, user: CurrentUser, svc=Depends(get_document_service)):
    doc = await svc.get_document(document_id)
    if not doc: raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return APIResponse(data=GeneratedDocumentResponse(**doc.model_dump()))


@router.post("/generated/{document_id}/approve", response_model=APIResponse)
async def approve_document(
    document_id: str,
    user: CurrentUser = Depends(require_permission("documents:approve")),
    svc=Depends(get_document_service),
):
    approved = await svc.approve_document(document_id, approved_by=user.user_id)
    if not approved: raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")
    return APIResponse(data=GeneratedDocumentResponse(**approved.model_dump()), message="Document approved")


# ── Report Schedules (Story 10) ───────────────────────────────


@router.get("/schedules", response_model=PaginatedResponse[ReportScheduleResponse])
async def list_report_schedules(
    pagination: Pagination, user: CurrentUser,
    is_active: bool | None = Query(None),
    svc=Depends(get_document_service),
):
    filters = {}
    if is_active is not None: filters["is_active"] = is_active
    schedules, total = await svc.list_schedules(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [ReportScheduleResponse(**s.model_dump()) for s in schedules]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/schedules", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_report_schedule(
    request: ReportScheduleCreateRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_document_service),
):
    """Create an automated report schedule (Story 10)."""
    schedule = await svc.create_report_schedule(request.model_dump())
    return APIResponse(data=ReportScheduleResponse(**schedule.model_dump()), message="Report schedule created")


@router.get("/schedules/{schedule_id}", response_model=APIResponse)
async def get_report_schedule(schedule_id: str, user: CurrentUser, svc=Depends(get_document_service)):
    schedule = await svc.get_schedule(schedule_id)
    if not schedule: raise HTTPException(status_code=404, detail=f"Schedule '{schedule_id}' not found")
    return APIResponse(data=ReportScheduleResponse(**schedule.model_dump()))


# ── Excel Templates (Stories 6, 7) ────────────────────────────


@router.get("/excel-templates", response_model=PaginatedResponse[ExcelTemplateResponse])
async def list_excel_templates(
    pagination: Pagination, user: CurrentUser,
    source: str | None = Query(None),
    svc=Depends(get_excel_service),
):
    filters = {}
    if source: filters["source"] = source
    templates, total = await svc.list_templates(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [ExcelTemplateResponse(**t.model_dump()) for t in templates]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/excel-templates", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_excel_template(
    request: ExcelTemplateCreateRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_excel_service),
):
    template = await svc.create_template(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=ExcelTemplateResponse(**template.model_dump()), message="Excel template created")


@router.post("/excel-templates/import", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def import_excel_template(
    request: ExcelTemplateImportRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_excel_service),
):
    """Import an existing Excel template (Story 7)."""
    template = await svc.import_template(
        name=request.name, file_url=request.file_url,
        sheet_definitions=request.sheet_definitions,
    )
    return APIResponse(data=ExcelTemplateResponse(**template.model_dump()), message="Excel template imported")


@router.get("/excel-templates/{template_id}", response_model=APIResponse)
async def get_excel_template(template_id: str, user: CurrentUser, svc=Depends(get_excel_service)):
    template = await svc.get_template(template_id)
    if not template: raise HTTPException(status_code=404, detail=f"Excel template '{template_id}' not found")
    return APIResponse(data=ExcelTemplateResponse(**template.model_dump()))


@router.patch("/excel-templates/{template_id}", response_model=APIResponse)
async def update_excel_template(
    template_id: str, request: ExcelTemplateCreateRequest,
    user: CurrentUser = Depends(require_permission("documents:write")),
    svc=Depends(get_excel_service),
):
    updated = await svc.update_template(template_id, request.model_dump(exclude_unset=True))
    if not updated: raise HTTPException(status_code=404, detail=f"Excel template '{template_id}' not found")
    return APIResponse(data=ExcelTemplateResponse(**updated.model_dump()))
