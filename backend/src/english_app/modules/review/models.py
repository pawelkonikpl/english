from datetime import UTC, date, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class ReviewItem(SQLModel, table=True):
    """Spaced-repetition state of one learnable item, independent of its content."""

    __tablename__ = "review_item"
    __table_args__ = (UniqueConstraint("item_type", "item_id"),)

    id: int | None = Field(default=None, primary_key=True)
    item_type: str = Field(max_length=40, index=True)
    item_id: int = Field(index=True)
    step: int = 0
    interval_days: int = 0
    due_on: date = Field(index=True)
    mastery: int = 0
    lapses: int = 0
    reviews_count: int = 0
    last_reviewed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now, index=True)


class ReviewLog(SQLModel, table=True):
    __tablename__ = "review_log"

    id: int | None = Field(default=None, primary_key=True)
    review_item_id: int = Field(foreign_key="review_item.id", index=True)
    grade: str = Field(max_length=10)
    mode: str = Field(max_length=20)
    step_before: int
    step_after: int
    reviewed_at: datetime = Field(default_factory=utc_now, index=True)
