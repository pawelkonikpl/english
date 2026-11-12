from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

ITEM_TYPE = "phrase"  # item type used in the review module


def utc_now() -> datetime:
    return datetime.now(UTC)


class PhraseKind(StrEnum):
    PHRASE = "phrase"
    PHRASAL_VERB = "phrasal_verb"
    WORD = "word"
    FALSE_FRIEND = "false_friend"
    COMMON_ERROR = "common_error"


class PhraseSource(StrEnum):
    SEED = "seed"
    AI = "ai"
    USER = "user"


class Phrase(SQLModel, table=True):
    __tablename__ = "phrase"
    __table_args__ = (UniqueConstraint("section_code", "english"),)

    id: int | None = Field(default=None, primary_key=True)
    tier: str = Field(max_length=20, index=True)
    tier_title: str = Field(max_length=200)
    section_code: str = Field(max_length=20, index=True)
    section_title: str = Field(max_length=200)
    position: int = Field(index=True)
    english: str = Field(max_length=500)
    polish: str = Field(max_length=500)
    example: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=1000)
    kind: PhraseKind = PhraseKind.PHRASE
    source: PhraseSource = PhraseSource.SEED
    ai_explanation: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    ai_explanation_model: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)
