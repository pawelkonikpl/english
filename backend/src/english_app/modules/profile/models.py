from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

PROFILE_ID = 1


def utc_now() -> datetime:
    return datetime.now(UTC)


class CefrLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class LearnerProfile(SQLModel, table=True):
    __tablename__ = "learner_profile"

    id: int = Field(default=PROFILE_ID, primary_key=True)
    display_name: str | None = Field(default=None, max_length=100)
    level: CefrLevel = Field(default=CefrLevel.A2)
    target_level: CefrLevel | None = None
    native_language: str = Field(default="pl", max_length=10)
    goals: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    daily_goal_xp: int = Field(default=30, ge=5, le=500)
    onboarding_done: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
