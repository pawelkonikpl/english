from collections.abc import Sequence

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.lessons.models import (
    Lesson,
    LessonAnswer,
    LessonStatus,
    LessonType,
    LessonWord,
)


class LessonRepository:
    """Queries for lessons, answers and lesson words. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, lesson_id: int) -> Lesson | None:
        return await self._session.get(Lesson, lesson_id)

    async def recent(self, limit: int, exclude: LessonType | None = None) -> list[Lesson]:
        statement = select(Lesson).order_by(col(Lesson.created_at).desc()).limit(limit)
        if exclude is not None:
            statement = statement.where(Lesson.type != exclude)
        return list((await self._session.exec(statement)).all())

    async def topics(self, lesson_type: LessonType) -> set[str]:
        statement = select(Lesson.topic).where(
            Lesson.type == lesson_type, Lesson.status == LessonStatus.COMPLETED
        )
        return set((await self._session.exec(statement)).all())

    async def answers(self, lesson_id: int) -> list[LessonAnswer]:
        statement = select(LessonAnswer).where(LessonAnswer.lesson_id == lesson_id)
        return list((await self._session.exec(statement)).all())

    async def words(self, lesson_id: int) -> list[LessonWord]:
        statement = (
            select(LessonWord).where(LessonWord.lesson_id == lesson_id).order_by(col(LessonWord.id))
        )
        return list((await self._session.exec(statement)).all())

    async def words_by_ids(self, ids: Sequence[int]) -> list[LessonWord]:
        if not ids:
            return []
        statement = select(LessonWord).where(col(LessonWord.id).in_(ids))
        return list((await self._session.exec(statement)).all())

    async def recent_words(self, limit: int) -> list[str]:
        statement = select(LessonWord.word).order_by(col(LessonWord.id).desc()).limit(limit)
        return list((await self._session.exec(statement)).all())

    def add(self, entity: Lesson | LessonAnswer | LessonWord) -> None:
        self._session.add(entity)
