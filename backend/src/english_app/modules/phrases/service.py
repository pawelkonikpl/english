from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.errors import NotFoundError
from english_app.core.events import ActivityKind, EventBus, LearningActivity
from english_app.core.prompts import PromptRenderer
from english_app.llm.base import ChatMessage, ModelTier
from english_app.llm.service import LLMService
from english_app.modules.phrases.models import ITEM_TYPE, Phrase
from english_app.modules.phrases.repository import PhraseRepository
from english_app.modules.phrases.schemas import PhraseExplanation, PhraseStatus
from english_app.modules.profile.public import get_learner_context
from english_app.modules.review import public as review

PROMPTS = PromptRenderer(Path(__file__).parent / "prompts")
MASTERED = 3


class PhraseNotFoundError(NotFoundError):
    def __init__(self, phrase_id: int) -> None:
        super().__init__(f"Phrase {phrase_id} not found", user_message="Nie znaleziono frazy.")


@dataclass(frozen=True)
class PhraseWithState:
    phrase: Phrase
    state: review.ReviewState | None

    @property
    def status(self) -> PhraseStatus:
        if self.state is None:
            return PhraseStatus.NEW
        return PhraseStatus.MASTERED if self.state.mastery >= MASTERED else PhraseStatus.LEARNING


@dataclass(frozen=True)
class Section:
    tier: str
    tier_title: str
    code: str
    title: str
    total: int
    learning: int
    mastered: int


@dataclass(frozen=True)
class LearnSession:
    daily_limit: int
    remaining_today: int
    phrases: list[PhraseWithState]


class PhraseService:
    def __init__(
        self, session: AsyncSession, clock: Clock, bus: EventBus, daily_new_limit: int
    ) -> None:
        self._session = session
        self._clock = clock
        self._bus = bus
        self._daily_new_limit = daily_new_limit
        self._phrases = PhraseRepository(session)

    async def list_phrases(
        self, section_code: str | None = None, status: PhraseStatus | None = None
    ) -> list[PhraseWithState]:
        items = await self._with_state(await self._phrases.all_ordered(section_code))
        return [item for item in items if status is None or item.status is status]

    async def sections(self) -> list[Section]:
        counts: dict[str, Counter[PhraseStatus]] = {}
        first: dict[str, Phrase] = {}
        for item in await self._with_state(await self._phrases.all_ordered()):
            code = item.phrase.section_code
            first.setdefault(code, item.phrase)
            counts.setdefault(code, Counter())[item.status] += 1
        return [
            Section(
                tier=phrase.tier,
                tier_title=phrase.tier_title,
                code=code,
                title=phrase.section_title,
                total=counts[code].total(),
                learning=counts[code][PhraseStatus.LEARNING],
                mastered=counts[code][PhraseStatus.MASTERED],
            )
            for code, phrase in first.items()
        ]

    async def learn_session(self) -> LearnSession:
        start, end = self._clock.day_bounds(self._clock.today())
        enrolled_today = await review.count_enrolled_between(self._session, ITEM_TYPE, start, end)
        remaining = max(self._daily_new_limit - enrolled_today, 0)
        new_phrases = [
            item for item in await self.list_phrases() if item.status is PhraseStatus.NEW
        ]
        return LearnSession(self._daily_new_limit, remaining, new_phrases[:remaining])

    async def enroll(self, phrase_id: int, *, known: bool) -> tuple[PhraseWithState, int, bool]:
        phrase = await self._get(phrase_id)
        item, created = await review.enroll(
            self._session, self._clock, ITEM_TYPE, phrase_id, known=known
        )
        if created:
            await self._bus.publish(
                LearningActivity(
                    kind=ActivityKind.PHRASE_ENROLLED,
                    ref_type=ITEM_TYPE,
                    ref_id=phrase_id,
                    details={"known": known},
                ),
                self._session,
            )
        await self._session.commit()
        [with_state] = await self._with_state([phrase])
        return with_state, item.id or 0, created

    async def explain(
        self, phrase_id: int, llm: LLMService, *, regenerate: bool
    ) -> tuple[PhraseExplanation, str | None, bool]:
        phrase = await self._get(phrase_id)
        if phrase.ai_explanation is not None and not regenerate:
            explanation = PhraseExplanation.model_validate(phrase.ai_explanation)
            return explanation, phrase.ai_explanation_model, True

        learner = await get_learner_context(self._session)
        system = PROMPTS.render(
            "explain.md",
            level=learner.level.value,
            native_language=learner.native_language_name,
            english=phrase.english,
            polish=phrase.polish,
            example=phrase.example,
            note=phrase.note,
        )
        result = await llm.complete_structured(
            system=system,
            messages=[ChatMessage(role="user", content=f"Explain: {phrase.english}")],
            schema=PhraseExplanation,
            tier=ModelTier.FAST,
        )
        phrase.ai_explanation = result.value.model_dump()
        phrase.ai_explanation_model = result.model
        self._phrases.add(phrase)
        await self._session.commit()
        return result.value, result.model, False

    async def _get(self, phrase_id: int) -> Phrase:
        phrase = await self._phrases.get(phrase_id)
        if phrase is None:
            raise PhraseNotFoundError(phrase_id)
        return phrase

    async def _with_state(self, phrases: list[Phrase]) -> list[PhraseWithState]:
        ids = [p.id for p in phrases if p.id is not None]
        states = await review.states(self._session, ITEM_TYPE, ids)
        return [PhraseWithState(p, states.get(p.id or 0)) for p in phrases]
