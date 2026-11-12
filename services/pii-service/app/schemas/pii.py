"""Request and response models of the PII endpoints."""

from typing import Self

from pydantic import BaseModel, Field

from app.detectors.base import PiiCategory, PiiEntity

MAX_TEXT_CHARS = 200_000


class PiiRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS, description="Text to analyse.")
    categories: list[PiiCategory] | None = Field(
        default=None,
        min_length=1,
        description="Only handle these categories. All categories when omitted.",
    )
    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for this request. The service default when omitted.",
    )


class PiiEntityResponse(BaseModel):
    category: PiiCategory
    source_label: str = Field(description="Label reported by the detector backend.")
    start: int = Field(description="Offset of the first character in the request text.")
    end: int = Field(description="Offset one past the last character in the request text.")
    text: str
    score: float

    @classmethod
    def from_entity(cls, entity: PiiEntity, source_text: str) -> Self:
        return cls(
            category=entity.category,
            source_label=entity.source_label,
            start=entity.start,
            end=entity.end,
            text=source_text[entity.start : entity.end],
            score=entity.score,
        )


class DetectResponse(BaseModel):
    backend: str
    entities: list[PiiEntityResponse]


class RedactResponse(BaseModel):
    backend: str
    redacted_text: str
    entities: list[PiiEntityResponse] = Field(
        description="Redacted entities; offsets refer to the request text."
    )
