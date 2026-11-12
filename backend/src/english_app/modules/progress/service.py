import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.events import ActivityKind, LearningActivity
from english_app.modules.profile.public import get_learner_context
from english_app.modules.progress.models import AchievementUnlock, Activity
from english_app.modules.progress.repository import ProgressRepository
from english_app.modules.progress.rules import (
    ACHIEVEMENTS,
    SAME_TYPE_LIMIT,
    Achievement,
    ProgressStats,
    Recommendation,
    RecommendationInput,
    Streak,
    compute_streak,
    points_for,
    recommend,
)
from english_app.modules.review import public as review

ACHIEVEMENTS_BY_KEY = {a.key: a for a in ACHIEVEMENTS}


@dataclass(frozen=True)
class DayActivity:
    day: date
    xp: int
    count: int


@dataclass(frozen=True)
class AchievementState:
    achievement: Achievement
    unlock: AchievementUnlock | None


@dataclass(frozen=True)
class Dashboard:
    display_name: str | None
    level: str
    daily_goal_xp: int
    xp_today: int
    xp_total: int
    streak: Streak
    reviews_due: int
    mastery_counts: dict[tuple[str, int], int]
    recommendation: Recommendation | None
    new_achievements: list[AchievementState]


class ProgressService:
    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self._session = session
        self._clock = clock
        self._progress = ProgressRepository(session)

    async def record(self, activity: LearningActivity) -> None:
        """Store an activity and unlock achievements. Runs inside the publisher's transaction."""
        self._progress.add(
            Activity(
                kind=activity.kind.value,
                points=points_for(activity),
                ref_type=activity.ref_type,
                ref_id=activity.ref_id,
                details=dict(activity.details),
                occurred_at=self._clock.now(),
            )
        )
        await self._session.flush()
        await self._unlock_new_achievements()

    async def dashboard(self, enabled_modules: frozenset[str]) -> Dashboard:
        today = self._clock.today()
        learner = await get_learner_context(self._session)
        review_summary = await review.summary(self._session, today)
        start, _ = self._clock.day_bounds(today)
        today_activities = await self._progress.activities_since(start)
        unlocks = await self._progress.unlocks()
        return Dashboard(
            display_name=learner.display_name,
            level=learner.level.value,
            daily_goal_xp=learner.daily_goal_xp,
            xp_today=math.floor(sum(a.points for a in today_activities)),
            xp_total=math.floor(await self._progress.total_points()),
            streak=await self._streak(),
            reviews_due=review_summary.due_today,
            mastery_counts=review_summary.mastery_counts,
            recommendation=recommend(
                RecommendationInput(
                    due_reviews=review_summary.due_today,
                    phrases_enrolled_today=sum(
                        1 for a in today_activities if a.kind == ActivityKind.PHRASE_ENROLLED
                    ),
                    recent_lesson_types=await self._progress.recent_lesson_types(SAME_TYPE_LIMIT),
                    enabled_modules=enabled_modules,
                )
            ),
            new_achievements=[
                AchievementState(ACHIEVEMENTS_BY_KEY[u.achievement_key], u)
                for u in unlocks
                if not u.seen and u.achievement_key in ACHIEVEMENTS_BY_KEY
            ],
        )

    async def activity(self, days: int) -> list[DayActivity]:
        today = self._clock.today()
        first_day = today - timedelta(days=days - 1)
        start, _ = self._clock.day_bounds(first_day)
        xp: dict[date, float] = defaultdict(float)
        count: dict[date, int] = defaultdict(int)
        for item in await self._progress.activities_since(start):
            day = self._clock.local_date(item.occurred_at)
            xp[day] += item.points
            count[day] += 1
        return [
            DayActivity(day=day, xp=math.floor(xp[day]), count=count[day])
            for day in (first_day + timedelta(days=offset) for offset in range(days))
        ]

    async def achievements(self) -> list[AchievementState]:
        unlocks = {u.achievement_key: u for u in await self._progress.unlocks()}
        return [AchievementState(a, unlocks.get(a.key)) for a in ACHIEVEMENTS]

    async def mark_achievements_seen(self) -> None:
        for unlock in await self._progress.unlocks():
            if not unlock.seen:
                unlock.seen = True
                self._progress.add(unlock)
        await self._session.commit()

    async def _streak(self) -> Streak:
        times = await self._progress.activity_times()
        return compute_streak((self._clock.local_date(t) for t in times), self._clock.today())

    async def _stats(self) -> ProgressStats:
        counts = await self._progress.count_by_kind()
        streak = await self._streak()
        return ProgressStats(
            phrases_enrolled=counts.get(ActivityKind.PHRASE_ENROLLED, 0),
            reviews_done=counts.get(ActivityKind.REVIEW_GRADED, 0),
            lessons_completed=counts.get(ActivityKind.LESSON_COMPLETED, 0),
            conversations_finished=counts.get(ActivityKind.CONVERSATION_FINISHED, 0),
            current_streak=streak.current,
            longest_streak=streak.longest,
            milestones=frozenset(await self._progress.milestones()),
        )

    async def _unlock_new_achievements(self) -> None:
        unlocked = {u.achievement_key for u in await self._progress.unlocks()}
        stats = await self._stats()
        for achievement in ACHIEVEMENTS:
            if achievement.key not in unlocked and achievement.is_unlocked(stats):
                self._progress.add(
                    AchievementUnlock(
                        achievement_key=achievement.key, unlocked_at=self._clock.now()
                    )
                )
