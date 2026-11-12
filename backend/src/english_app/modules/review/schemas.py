from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from english_app.modules.review.srs import Grade


class ReviewMode(StrEnum):
    RECOGNITION = "recognition"
    RECALL = "recall"
    SENTENCE = "sentence"


class CardResponse(BaseModel):
    front: str
    back: str
    example: str | None
    note: str | None
    label: str | None


class DueItemResponse(BaseModel):
    id: int
    item_type: str
    item_id: int
    step: int
    mastery: int
    due_on: date
    lapses: int
    card: CardResponse


class ReviewSummaryResponse(BaseModel):
    due_today: int
    total_reviews: int


class GradeRequest(BaseModel):
    grade: Grade
    mode: ReviewMode = ReviewMode.RECOGNITION


class GradeResponse(BaseModel):
    id: int
    step: int
    mastery: int
    interval_days: int
    due_on: date
    due_again_today: bool


class RecallCheckRequest(BaseModel):
    answer: str = Field(max_length=500)


class RecallCheckResponse(BaseModel):
    correct: bool
    expected: str


class SentenceCheckRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=1000)


class SentenceCheck(BaseModel):
    """Structured LLM output for the 'use it in a sentence' mode."""

    correct: bool
    uses_phrase: bool
    corrected_sentence: str
    explanation: str


class SentenceCheckResponse(SentenceCheck):
    model: str | None
