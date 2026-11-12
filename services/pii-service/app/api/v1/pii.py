"""PII detection and redaction endpoints.

The handlers are sync on purpose: inference is CPU-bound, and FastAPI runs sync
handlers in a thread pool instead of blocking the event loop.
"""

from fastapi import APIRouter, status

from app.dependencies import PiiServiceDep
from app.schemas.pii import DetectResponse, PiiEntityResponse, PiiRequest, RedactResponse

router = APIRouter(prefix="/pii", tags=["pii"])


@router.post("/detect", response_model=DetectResponse, status_code=status.HTTP_200_OK)
def detect_pii(payload: PiiRequest, service: PiiServiceDep) -> DetectResponse:
    entities = service.detect(
        payload.text, categories=payload.categories, min_score=payload.min_score
    )
    return DetectResponse(
        backend=service.backend,
        entities=[PiiEntityResponse.from_entity(entity, payload.text) for entity in entities],
    )


@router.post("/redact", response_model=RedactResponse, status_code=status.HTTP_200_OK)
def redact_pii(payload: PiiRequest, service: PiiServiceDep) -> RedactResponse:
    result = service.redact(
        payload.text, categories=payload.categories, min_score=payload.min_score
    )
    return RedactResponse(
        backend=service.backend,
        redacted_text=result.redacted_text,
        entities=[
            PiiEntityResponse.from_entity(entity, payload.text) for entity in result.entities
        ],
    )
