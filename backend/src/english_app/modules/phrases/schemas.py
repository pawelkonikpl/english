from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from english_app.modules.phrases.models import PhraseKind, PhraseSource


class PhraseStatus(StrEnum):
    NEW = "new"
    LEARNING = "learning"
    MASTERED = "mastered"


class SectionResponse(BaseModel):
    tier: str
    tier_title: str
    code: str
    title: str
    total: int
    learning: int
    mastered: int


class PhraseResponse(BaseModel):
    id: int
    tier: str
    section_code: str
    section_title: str
    english: str
    polish: str
    example: str | None
    note: str | None
    kind: PhraseKind
    source: PhraseSource
    status: PhraseStatus
    mastery: int
    due_on: date | None
    has_explanation: bool


class LearnSessionResponse(BaseModel):
    daily_limit: int
    remaining_today: int
    phrases: list[PhraseResponse]


class EnrollRequest(BaseModel):
    known: bool = False


class EnrollResponse(BaseModel):
    phrase_id: int
    review_item_id: int
    newly_enrolled: bool
    status: PhraseStatus


class ExplainRequest(BaseModel):
    regenerate: bool = False


class ExampleSentence(BaseModel):
    english: str
    translation: str


class PhraseExplanation(BaseModel):
    """Structured LLM output describing one phrase."""

    meaning: str
    when_to_use: str
    examples: list[ExampleSentence]
    similar: list[str]
    tip: str


class PhraseExplanationResponse(PhraseExplanation):
    model: str | None
    cached: bool
