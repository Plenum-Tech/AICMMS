"""Data connector management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from cafm.api.dependencies import Bus, CurrentUser, Manager, require_permission
from cafm.api.schemas.common import APIResponse
from cafm.api.schemas.connectors import (
    ConnectorCreateRequest,
    ConnectorResponse,
    ConnectorTestResult,
    QueryRequest,
    QueryResponse,
)
from cafm.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["Data Connectors"])


def _get_connector_service(manager: Manager, bus: Bus) -> ConnectorService:
    return ConnectorService(manager, bus)


@router.get("/", response_model=APIResponse)
async def list_connectors(
    user: CurrentUser,
    manager: Manager,
    bus: Bus,
):
    """List all active data source connectors."""
    svc = _get_connector_service(manager, bus)
    connectors = svc.list_connectors()
    return APIResponse(data=connectors)


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_connector(
    request: ConnectorCreateRequest,
    manager: Manager,
    bus: Bus,
    user: CurrentUser = Depends(require_permission("connectors:write")),
):
    """Register and connect a new data source."""
    svc = _get_connector_service(manager, bus)
    try:
        result = await svc.add_connector(
            name=request.name,
            source_type=request.source_type,
            connection_params=request.connection_params,
            description=request.description,
        )
        return APIResponse(data=result, message=f"Connector '{request.name}' added successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{name}", response_model=APIResponse)
async def get_connector(
    name: str,
    user: CurrentUser,
    manager: Manager,
    bus: Bus,
):
    """Get details of a specific connector."""
    svc = _get_connector_service(manager, bus)
    info = svc.get_connector_info(name)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{name}' not found",
        )
    return APIResponse(data=info)


@router.delete("/{name}", response_model=APIResponse)
async def remove_connector(
    name: str,
    manager: Manager,
    bus: Bus,
    user: CurrentUser = Depends(require_permission("connectors:delete")),
):
    """Disconnect and remove a data source."""
    svc = _get_connector_service(manager, bus)
    try:
        await svc.remove_connector(name)
        return APIResponse(message=f"Connector '{name}' removed")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{name}/test", response_model=ConnectorTestResult)
async def test_connector(
    name: str,
    user: CurrentUser,
    manager: Manager,
    bus: Bus,
):
    """Test connectivity to a data source."""
    svc = _get_connector_service(manager, bus)
    result = await svc.test_connection(name)
    return ConnectorTestResult(**result)


@router.get("/{name}/schema", response_model=APIResponse)
async def get_connector_schema(
    name: str,
    refresh: bool = False,
    user: CurrentUser = Depends(require_permission("connectors:read")),
    manager: Manager = ...,
    bus: Bus = ...,
):
    """Discover the schema of a data source."""
    svc = _get_connector_service(manager, bus)
    try:
        schema = await svc.discover_schema(name, refresh=refresh)
        return APIResponse(data=schema.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_data_source(
    request: QueryRequest,
    user: CurrentUser,
    manager: Manager,
    bus: Bus,
):
    """Execute a query against a connected data source."""
    svc = _get_connector_service(manager, bus)
    try:
        result = await svc.query_source(
            source_name=request.source_name,
            table=request.table,
            columns=request.columns,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset,
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/types/available", response_model=APIResponse)
async def list_connector_types(
    user: CurrentUser,
    manager: Manager,
    bus: Bus,
):
    """List all registered connector plugin types."""
    svc = _get_connector_service(manager, bus)
    types = svc.list_registered_types()
    return APIResponse(data=types)
