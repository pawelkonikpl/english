"""Public API of the review module, used by modules that own learnable content.

Other modules may import only from this file.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.modules.review.cards import CardContent, CardLoader, register_card_loader
from english_app.modules.review.models import ReviewItem
from english_app.modules.review.repository import ReviewRepository
from english_app.modules.review.srs import initial_schedule, mastery_for


@dataclass(frozen=True)
class ReviewState:
    step: int
    mastery: int
    due_on: date
    reviews_count: int


@dataclass(frozen=True)
class ReviewSummary:
    due_today: int
    total_reviews: int
    mastery_counts: dict[tuple[str, int], int]
    """(item_type, mastery) -> number of items."""


async def enroll(
    session: AsyncSession, clock: Clock, item_type: str, item_id: int, *, known: bool
) -> tuple[ReviewItem, bool]:
    """Start reviewing an item. Idempotent; does not commit.

    Returns:
        The review item and whether it was newly created.
    """
    repository = ReviewRepository(session)
    existing = await repository.find(item_type, item_id)
    if existing is not None:
        return existing, False
    schedule = initial_schedule(known=known, today=clock.today())
    item = ReviewItem(
        item_type=item_type,
        item_id=item_id,
        step=schedule.step,
        interval_days=schedule.interval_days,
        due_on=schedule.due_on,
        mastery=mastery_for(schedule.step),
        created_at=clock.now(),
    )
    repository.add(item)
    await session.flush()
    return item, True


async def states(
    session: AsyncSession, item_type: str, item_ids: Sequence[int]
) -> dict[int, ReviewState]:
    items = await ReviewRepository(session).for_items(item_type, item_ids)
    return {
        item.item_id: ReviewState(
            step=item.step,
            mastery=item.mastery,
            due_on=item.due_on,
            reviews_count=item.reviews_count,
        )
        for item in items
    }


async def count_enrolled_between(
    session: AsyncSession, item_type: str, start: datetime, end: datetime
) -> int:
    return await ReviewRepository(session).count_created_between(item_type, start, end)


async def summary(session: AsyncSession, today: date) -> ReviewSummary:
    repository = ReviewRepository(session)
    return ReviewSummary(
        due_today=await repository.count_due(today),
        total_reviews=await repository.count_logs(),
        mastery_counts=await repository.mastery_counts(),
    )


__all__ = [
    "CardContent",
    "CardLoader",
    "ReviewState",
    "ReviewSummary",
    "count_enrolled_between",
    "enroll",
    "register_card_loader",
    "states",
    "summary",
]
