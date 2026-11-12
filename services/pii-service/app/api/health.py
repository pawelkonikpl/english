"""Health endpoint for load balancers and orchestrators."""

from fastapi import APIRouter, status

from app.dependencies import PiiServiceDep
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health(service: PiiServiceDep) -> HealthResponse:
    # The detector is loaded before the app accepts requests, so answering means ready.
    return HealthResponse(status="ok", backend=service.backend)
