from collections.abc import Sequence

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.phrases.models import Phrase


class PhraseRepository:
    """Queries for phrases. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, phrase_id: int) -> Phrase | None:
        return await self._session.get(Phrase, phrase_id)

    async def by_ids(self, phrase_ids: Sequence[int]) -> list[Phrase]:
        if not phrase_ids:
            return []
        statement = select(Phrase).where(col(Phrase.id).in_(phrase_ids))
        return list((await self._session.exec(statement)).all())

    async def all_ordered(self, section_code: str | None = None) -> list[Phrase]:
        statement = select(Phrase).order_by(col(Phrase.position), col(Phrase.id))
        if section_code is not None:
            statement = statement.where(Phrase.section_code == section_code)
        return list((await self._session.exec(statement)).all())

    async def find(self, section_code: str, english: str) -> Phrase | None:
        statement = select(Phrase).where(
            Phrase.section_code == section_code, Phrase.english == english
        )
        return (await self._session.exec(statement)).first()

    async def max_position(self) -> int:
        statement = select(func.max(Phrase.position))
        return int((await self._session.exec(statement)).one() or 0)

    def add(self, phrase: Phrase) -> None:
        self._session.add(phrase)
