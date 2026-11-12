"""Application factory of the PII service.

Run with: ``uvicorn app.main:create_app --factory``
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health
from app.api.v1 import pii
from app.config import Settings
from app.detectors.factory import DetectorFactory, create_default_factory
from app.services.pii_service import PiiService

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None, detector_factory: DetectorFactory | None = None
) -> FastAPI:
    """Build the app; the detector is created from ``settings.backend`` at startup."""
    resolved_settings = settings or Settings()
    resolved_factory = detector_factory or create_default_factory()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Loading the model here fails the startup on a bad configuration instead
        # of the first request, and keeps model loading out of request latency.
        detector = resolved_factory.create(resolved_settings.backend, resolved_settings)
        app.state.pii_service = PiiService(
            detector,
            backend=resolved_settings.backend,
            default_min_score=resolved_settings.min_score,
        )
        logger.info("PII detector ready (backend: %s)", resolved_settings.backend)
        yield

    app = FastAPI(title="PII Service", version="0.1.0", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(pii.router, prefix="/api/v1")
    return app
