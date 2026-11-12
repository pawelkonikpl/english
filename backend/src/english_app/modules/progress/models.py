from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Activity(SQLModel, table=True):
    """One learning action with the XP it earned. Source of streaks, XP and charts."""

    __tablename__ = "activity"

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(max_length=40, index=True)
    points: float = 0.0
    ref_type: str = Field(max_length=40)
    ref_id: int
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    occurred_at: datetime = Field(default_factory=utc_now, index=True)


class AchievementUnlock(SQLModel, table=True):
    __tablename__ = "achievement_unlock"

    id: int | None = Field(default=None, primary_key=True)
    achievement_key: str = Field(max_length=60, unique=True)
    unlocked_at: datetime = Field(default_factory=utc_now)
    seen: bool = False
