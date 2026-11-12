from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, SQLModel

WORD_ITEM_TYPE = "lesson_word"  # item type used in the review module


def utc_now() -> datetime:
    return datetime.now(UTC)


class LessonType(StrEnum):
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    WRITING = "writing"
    PLACEMENT = "placement"


class LessonStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Lesson(SQLModel, table=True):
    __tablename__ = "lesson"

    id: int | None = Field(default=None, primary_key=True)
    type: LessonType = Field(index=True)
    topic: str = Field(max_length=300)
    level: str = Field(max_length=4)
    content: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    status: LessonStatus = LessonStatus.IN_PROGRESS
    score: int | None = None
    max_score: int | None = None
    model: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now, index=True)
    completed_at: datetime | None = None


class LessonAnswer(SQLModel, table=True):
    __tablename__ = "lesson_answer"
    __table_args__ = (UniqueConstraint("lesson_id", "exercise_index"),)

    id: int | None = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lesson.id", index=True)
    exercise_index: int
    answer: str
    is_correct: bool
    feedback: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)


class LessonWord(SQLModel, table=True):
    __tablename__ = "lesson_word"

    id: int | None = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key="lesson.id", index=True)
    word: str = Field(max_length=200)
    phonetic: str | None = Field(default=None, max_length=200)
    translation: str = Field(max_length=300)
    mnemonic: str | None = Field(default=None, max_length=500)
    examples: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
