"""Public API of the phrases module, used by other modules.

Other modules may import only from this file.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.phrases.models import ITEM_TYPE
from english_app.modules.phrases.repository import PhraseRepository


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


__all__ = ["ITEM_TYPE", "PhraseText", "get_phrase_texts"]
