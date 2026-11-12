from datetime import datetime

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.progress.models import AchievementUnlock, Activity


class ProgressRepository:
    """Queries for activities and achievements. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, entity: Activity | AchievementUnlock) -> None:
        self._session.add(entity)

    async def activities_since(self, since: datetime) -> list[Activity]:
        statement = (
            select(Activity)
            .where(Activity.occurred_at >= since)
            .order_by(col(Activity.occurred_at))
        )
        return list((await self._session.exec(statement)).all())

    async def activity_times(self) -> list[datetime]:
        statement = select(Activity.occurred_at)
        return list((await self._session.exec(statement)).all())

    async def total_points(self) -> float:
        statement = select(func.coalesce(func.sum(Activity.points), 0.0))
        return float((await self._session.exec(statement)).one())

    async def count_by_kind(self) -> dict[str, int]:
        statement = select(Activity.kind, func.count()).group_by(col(Activity.kind))
        return {kind: int(count) for kind, count in (await self._session.exec(statement)).all()}

    async def milestones(self) -> set[str]:
        statement = select(Activity.details).where(Activity.kind == "milestone_reached")
        return {
            str(details.get("milestone"))
            for details in (await self._session.exec(statement)).all()
            if details.get("milestone")
        }

    async def recent_lesson_types(self, limit: int) -> list[str]:
        statement = (
            select(Activity.details)
            .where(Activity.kind == "lesson_completed")
            .order_by(col(Activity.occurred_at).desc())
            .limit(limit)
        )
        return [str(d.get("type")) for d in (await self._session.exec(statement)).all()]

    async def unlocks(self) -> list[AchievementUnlock]:
        statement = select(AchievementUnlock).order_by(col(AchievementUnlock.unlocked_at))
        return list((await self._session.exec(statement)).all())
