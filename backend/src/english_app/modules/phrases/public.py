"""Public API of the phrases module, used by other modules.

Other modules may import only from this file.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.events import ActivityKind, EventBus, LearningActivity
from english_app.modules.phrases.models import ITEM_TYPE, Phrase, PhraseKind, PhraseSource
from english_app.modules.phrases.repository import PhraseRepository
from english_app.modules.review import public as review

AI_TIER = "ai"
AI_TIER_TITLE = "Z rozmów i lekcji z AI"
AI_SECTION_CODE = "AI.1"
AI_SECTION_TITLE = "Frazy podsunięte przez AI"


@dataclass(frozen=True)
class PhraseText:
    id: int
    english: str
    polish: str


async def get_phrase_texts(session: AsyncSession, phrase_ids: Sequence[int]) -> list[PhraseText]:
    phrases = await PhraseRepository(session).by_ids(phrase_ids)
    by_id = {p.id: p for p in phrases if p.id is not None}
    return [
        PhraseText(id=pid, english=by_id[pid].english, polish=by_id[pid].polish)
        for pid in phrase_ids
        if pid in by_id
    ]


async def add_ai_phrase(
    session: AsyncSession,
    clock: Clock,
    bus: EventBus,
    *,
    english: str,
    polish: str,
    note: str | None = None,
) -> tuple[int, bool]:
    """Save a phrase suggested by AI and start reviewing it. Does not commit.

    Returns:
        The phrase id and whether it was newly enrolled in reviews.
    """
    repository = PhraseRepository(session)
    phrase = await repository.find(AI_SECTION_CODE, english.strip())
    if phrase is None:
        phrase = Phrase(
            tier=AI_TIER,
            tier_title=AI_TIER_TITLE,
            section_code=AI_SECTION_CODE,
            section_title=AI_SECTION_TITLE,
            position=await repository.max_position() + 1,
            english=english.strip(),
            polish=polish.strip(),
            note=note,
            kind=PhraseKind.PHRASE,
            source=PhraseSource.AI,
        )
        repository.add(phrase)
        await session.flush()
    phrase_id = phrase.id or 0
    _, created = await review.enroll(session, clock, ITEM_TYPE, phrase_id, known=False)
    if created:
        await bus.publish(
            LearningActivity(
                kind=ActivityKind.PHRASE_ENROLLED,
                ref_type=ITEM_TYPE,
                ref_id=phrase_id,
                details={"known": False, "source": "ai"},
            ),
            session,
        )
    return phrase_id, created


__all__ = ["ITEM_TYPE", "PhraseText", "add_ai_phrase", "get_phrase_texts"]
