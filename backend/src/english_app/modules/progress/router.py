from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from english_app.core.db import SessionDep
from english_app.core.dependencies import ClockDep
from english_app.core.modules import AppModule
from english_app.modules.progress.schemas import (
    AchievementResponse,
    DashboardResponse,
    DayActivityResponse,
    ItemProgressResponse,
    RecommendationResponse,
    StreakResponse,
    XpResponse,
)
from english_app.modules.progress.service import AchievementState, ProgressService

router = APIRouter(tags=["progress"])

FAMILIAR = 2
MASTERED = 3


def get_progress_service(session: SessionDep, clock: ClockDep) -> ProgressService:
    return ProgressService(session, clock)


ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]


def _achievement(state: AchievementState) -> AchievementResponse:
    a = state.achievement
    return AchievementResponse(
        key=a.key,
        title=a.title,
        description=a.description,
        icon=a.icon,
        unlocked_at=state.unlock.unlocked_at if state.unlock else None,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(request: Request, service: ProgressServiceDep) -> DashboardResponse:
    modules: list[AppModule] = request.app.state.modules
    data = await service.dashboard(frozenset(m.key for m in modules))
    item_types = sorted({item_type for item_type, _ in data.mastery_counts})
    rec = data.recommendation
    return DashboardResponse(
        display_name=data.display_name,
        level=data.level,
        streak=StreakResponse(
            current=data.streak.current,
            longest=data.streak.longest,
            active_today=data.streak.active_today,
        ),
        xp=XpResponse(today=data.xp_today, goal=data.daily_goal_xp, total=data.xp_total),
        reviews_due=data.reviews_due,
        items=[
            ItemProgressResponse(
                item_type=item_type,
                learning=sum(
                    n
                    for (t, m), n in data.mastery_counts.items()
                    if t == item_type and m < FAMILIAR
                ),
                familiar=data.mastery_counts.get((item_type, FAMILIAR), 0),
                mastered=data.mastery_counts.get((item_type, MASTERED), 0),
            )
            for item_type in item_types
        ],
        recommendation=RecommendationResponse(
            target=rec.target, lesson_type=rec.lesson_type, title=rec.title, reason=rec.reason
        )
        if rec
        else None,
        new_achievements=[_achievement(s) for s in data.new_achievements],
    )


@router.get("/activity", response_model=list[DayActivityResponse])
async def get_activity(
    service: ProgressServiceDep, days: Annotated[int, Query(ge=1, le=366)] = 84
) -> list[DayActivityResponse]:
    return [
        DayActivityResponse(date=d.day, xp=d.xp, count=d.count)
        for d in await service.activity(days)
    ]


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(service: ProgressServiceDep) -> list[AchievementResponse]:
    return [_achievement(s) for s in await service.achievements()]


@router.post("/achievements/seen", status_code=status.HTTP_204_NO_CONTENT)
async def mark_seen(service: ProgressServiceDep) -> None:
    await service.mark_achievements_seen()
