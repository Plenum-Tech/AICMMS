"""Sensors and IoT device management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafm.api.dependencies import CurrentUser, Pagination, require_permission
from cafm.api.schemas.common import APIResponse, PaginatedResponse
from cafm.api.schemas.sensors import (
    DeviceCreateRequest, DeviceResponse,
    SensorReadingInput, SensorReadingResponse,
    ThresholdResponse,
)

router = APIRouter(prefix="/sensors", tags=["Sensors & IoT"])

_sensor_service = None


def get_sensor_service():
    if _sensor_service is None:
        raise HTTPException(status_code=503, detail="Sensor service not initialized")
    return _sensor_service


def set_sensor_service(svc) -> None:
    global _sensor_service
    _sensor_service = svc


# ── IoT Devices ───────────────────────────────────────────────


@router.get("/devices", response_model=PaginatedResponse[DeviceResponse])
async def list_devices(
    pagination: Pagination, user: CurrentUser,
    building_id: str | None = Query(None), asset_id: str | None = Query(None),
    device_status: str | None = Query(None, alias="status"),
    svc=Depends(get_sensor_service),
):
    filters = {}
    if building_id: filters["building_id"] = building_id
    if asset_id: filters["asset_id"] = asset_id
    if device_status: filters["status"] = device_status
    devices, total = await svc.list_devices(filters=filters or None, limit=pagination.limit, offset=pagination.offset)
    items = [DeviceResponse(**d.model_dump()) for d in devices]
    return PaginatedResponse.create(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/devices", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    request: DeviceCreateRequest,
    user: CurrentUser = Depends(require_permission("sensors:write")),
    svc=Depends(get_sensor_service),
):
    device = await svc.create_device(request.model_dump(), created_by=user.user_id)
    return APIResponse(data=DeviceResponse(**device.model_dump()), message=f"Device '{device.device_id}' registered")


@router.get("/devices/{device_id}", response_model=APIResponse)
async def get_device(device_id: str, user: CurrentUser, svc=Depends(get_sensor_service)):
    device = await svc.get_device(device_id)
    if not device: raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return APIResponse(data=DeviceResponse(**device.model_dump()))


# ── Sensor Readings ───────────────────────────────────────────


@router.post("/readings", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def ingest_reading(
    request: SensorReadingInput,
    user: CurrentUser = Depends(require_permission("sensors:write")),
    svc=Depends(get_sensor_service),
):
    """Ingest a sensor reading. Triggers threshold checks and anomaly detection."""
    reading = await svc.ingest_reading(request.model_dump())
    return APIResponse(data=SensorReadingResponse(**reading.model_dump()), message="Reading ingested")


@router.post("/readings/batch", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def ingest_readings_batch(
    readings: list[SensorReadingInput],
    user: CurrentUser = Depends(require_permission("sensors:write")),
    svc=Depends(get_sensor_service),
):
    """Ingest multiple sensor readings in a batch."""
    results = await svc.ingest_readings_batch([r.model_dump() for r in readings])
    return APIResponse(data={"ingested": len(results)}, message=f"{len(results)} reading(s) ingested")


@router.get("/readings/{device_id}", response_model=APIResponse)
async def get_device_readings(
    device_id: str, user: CurrentUser,
    limit: int = Query(100, ge=1, le=1000),
    svc=Depends(get_sensor_service),
):
    readings, total = await svc.get_device_readings(device_id, limit=limit)
    items = [SensorReadingResponse(**r.model_dump()) for r in readings]
    return APIResponse(data={"readings": items, "total": total})


@router.get("/readings/{device_id}/latest", response_model=APIResponse)
async def get_latest_reading(device_id: str, user: CurrentUser, svc=Depends(get_sensor_service)):
    reading = await svc.get_latest_reading(device_id)
    if not reading: raise HTTPException(status_code=404, detail=f"No readings for device '{device_id}'")
    return APIResponse(data=SensorReadingResponse(**reading.model_dump()))


# ── Thresholds ────────────────────────────────────────────────


@router.get("/thresholds/{device_id}", response_model=APIResponse)
async def get_device_thresholds(device_id: str, user: CurrentUser, svc=Depends(get_sensor_service)):
    thresholds = await svc.get_thresholds(device_id)
    items = [ThresholdResponse(**t.model_dump()) for t in thresholds]
    return APIResponse(data=items)
