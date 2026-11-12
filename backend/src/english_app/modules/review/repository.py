from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.review.models import ReviewItem, ReviewLog


class ReviewRepository:
    """Queries for review items and logs. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, review_item_id: int) -> ReviewItem | None:
        return await self._session.get(ReviewItem, review_item_id)

    async def find(self, item_type: str, item_id: int) -> ReviewItem | None:
        statement = select(ReviewItem).where(
            ReviewItem.item_type == item_type, ReviewItem.item_id == item_id
        )
        return (await self._session.exec(statement)).first()

    async def for_items(self, item_type: str, item_ids: Sequence[int]) -> list[ReviewItem]:
        if not item_ids:
            return []
        statement = select(ReviewItem).where(
            ReviewItem.item_type == item_type, col(ReviewItem.item_id).in_(item_ids)
        )
        return list((await self._session.exec(statement)).all())

    async def due(self, today: date, limit: int) -> list[ReviewItem]:
        statement = (
            select(ReviewItem)
            .where(ReviewItem.due_on <= today)
            .order_by(col(ReviewItem.due_on), col(ReviewItem.id))
            .limit(limit)
        )
        return list((await self._session.exec(statement)).all())

    async def count_due(self, today: date) -> int:
        statement = select(func.count()).select_from(ReviewItem).where(ReviewItem.due_on <= today)
        return int((await self._session.exec(statement)).one())

    async def count_created_between(self, item_type: str, start: datetime, end: datetime) -> int:
        statement = (
            select(func.count())
            .select_from(ReviewItem)
            .where(
                ReviewItem.item_type == item_type,
                ReviewItem.created_at >= start,
                ReviewItem.created_at < end,
            )
        )
        return int((await self._session.exec(statement)).one())

    async def mastery_counts(self) -> dict[tuple[str, int], int]:
        statement = select(ReviewItem.item_type, ReviewItem.mastery, func.count()).group_by(
            col(ReviewItem.item_type), col(ReviewItem.mastery)
        )
        rows = (await self._session.exec(statement)).all()
        return {(item_type, mastery): int(count) for item_type, mastery, count in rows}

    async def count_logs(self) -> int:
        statement = select(func.count()).select_from(ReviewLog)
        return int((await self._session.exec(statement)).one())

    def add(self, item: ReviewItem) -> None:
        self._session.add(item)

    def add_log(self, log: ReviewLog) -> None:
        self._session.add(log)
