from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: int | None = Field(default=None, primary_key=True)
    scenario_key: str = Field(max_length=60)
    title: str = Field(max_length=200)
    topic: str | None = Field(default=None, max_length=300)
    level: str = Field(max_length=4)
    status: ConversationStatus = ConversationStatus.ACTIVE
    target_phrase_ids: list[int] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    score: int | None = None
    summary: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    summary_model: str | None = Field(default=None, max_length=100)
    started_at: datetime = Field(default_factory=utc_now, index=True)
    finished_at: datetime | None = None


class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_message"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=10)  # "user" | "assistant"
    content: str
    feedback: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    model: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=utc_now)
