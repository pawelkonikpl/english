from dataclasses import dataclass
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.errors import NotFoundError
from english_app.core.events import ActivityKind, EventBus, LearningActivity
from english_app.core.prompts import PromptRenderer
from english_app.llm.base import ChatMessage, LLMResult, ModelTier
from english_app.llm.service import LLMService
from english_app.modules.profile.public import get_learner_context
from english_app.modules.review.cards import CardContent, load_cards
from english_app.modules.review.matching import is_correct
from english_app.modules.review.models import ReviewItem, ReviewLog
from english_app.modules.review.repository import ReviewRepository
from english_app.modules.review.schemas import ReviewMode, SentenceCheck
from english_app.modules.review.srs import Grade, mastery_for, next_schedule

PROMPTS = PromptRenderer(Path(__file__).parent / "prompts")


class ReviewItemNotFoundError(NotFoundError):
    def __init__(self, review_item_id: int) -> None:
        super().__init__(
            f"Review item {review_item_id} not found",
            user_message="Nie znaleziono tej pozycji w powtórkach.",
        )


@dataclass(frozen=True)
class DueCard:
    item: ReviewItem
    card: CardContent


class ReviewService:
    def __init__(self, session: AsyncSession, clock: Clock, bus: EventBus) -> None:
        self._session = session
        self._clock = clock
        self._bus = bus
        self._items = ReviewRepository(session)

    async def due_cards(self, limit: int) -> list[DueCard]:
        items = await self._items.due(self._clock.today(), limit)
        cards = await load_cards(self._session, [(i.item_type, i.item_id) for i in items])
        return [
            DueCard(item=item, card=cards[(item.item_type, item.item_id)])
            for item in items
            if (item.item_type, item.item_id) in cards
        ]

    async def grade(self, review_item_id: int, grade: Grade, mode: ReviewMode) -> ReviewItem:
        item = await self._get(review_item_id)
        schedule = next_schedule(item.step, grade, self._clock.today())
        self._items.add_log(
            ReviewLog(
                review_item_id=review_item_id,
                grade=grade.value,
                mode=mode.value,
                step_before=item.step,
                step_after=schedule.step,
                reviewed_at=self._clock.now(),
            )
        )
        item.step = schedule.step
        item.interval_days = schedule.interval_days
        item.due_on = schedule.due_on
        item.mastery = mastery_for(schedule.step)
        item.lapses += int(schedule.lapsed)
        item.reviews_count += 1
        item.last_reviewed_at = self._clock.now()
        self._items.add(item)
        await self._bus.publish(
            LearningActivity(
                kind=ActivityKind.REVIEW_GRADED,
                ref_type=item.item_type,
                ref_id=item.item_id,
                details={"grade": grade.value, "mode": mode.value, "mastery": item.mastery},
            ),
            self._session,
        )
        await self._session.commit()
        await self._session.refresh(item)
        return item

    async def check_recall(self, review_item_id: int, answer: str) -> tuple[bool, str]:
        card = await self._card(review_item_id)
        return is_correct(card.front, answer), card.front

    async def check_sentence(
        self, review_item_id: int, sentence: str, llm: LLMService
    ) -> LLMResult[SentenceCheck]:
        card = await self._card(review_item_id)
        learner = await get_learner_context(self._session)
        system = PROMPTS.render(
            "sentence_check.md",
            level=learner.level.value,
            native_language=learner.native_language_name,
            phrase=card.front,
            meaning=card.back,
        )
        return await llm.complete_structured(
            system=system,
            messages=[ChatMessage(role="user", content=sentence)],
            schema=SentenceCheck,
            tier=ModelTier.FAST,
        )

    async def _get(self, review_item_id: int) -> ReviewItem:
        item = await self._items.get(review_item_id)
        if item is None:
            raise ReviewItemNotFoundError(review_item_id)
        return item

    async def _card(self, review_item_id: int) -> CardContent:
        item = await self._get(review_item_id)
        cards = await load_cards(self._session, [(item.item_type, item.item_id)])
        card = cards.get((item.item_type, item.item_id))
        if card is None:
            raise ReviewItemNotFoundError(review_item_id)
        return card
