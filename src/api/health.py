"""Health check endpoints."""

import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    kafka_ready: bool
    kafka_status: str
    consumers_running: int
    version: str


@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check(
    request: Request,
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """Health check endpoint.

    Returns the health status of the application and its dependencies.

    Returns:
        Health check response
    """
    # Get Kafka status from app state
    kafka_ready = getattr(request.app.state, "kafka_ready", False)
    consumers = getattr(request.app.state, "consumers", [])
    
    if kafka_ready:
        kafka_status = "connected"
        status = "healthy"
    else:
        kafka_status = "initializing"
        status = "starting"

    return HealthResponse(
        status=status,
        kafka_ready=kafka_ready,
        kafka_status=kafka_status,
        consumers_running=len(consumers),
        version="0.1.0",
    )


@router.get("/ready", summary="Readiness Check")
async def readiness_check(request: Request, settings: Settings = Depends(get_settings)) -> dict:
    """Readiness check for Kubernetes/orchestration.

    Returns:
        Readiness status
    """
    kafka_ready = getattr(request.app.state, "kafka_ready", False)
    return {"ready": kafka_ready}


@router.get("/live", summary="Liveness Check")
async def liveness_check() -> dict:
    """Liveness check for Kubernetes/orchestration.

    Returns:
        Liveness status
    """
    return {"alive": True}
