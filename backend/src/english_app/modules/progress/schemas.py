from datetime import date, datetime

from pydantic import BaseModel


class StreakResponse(BaseModel):
    current: int
    longest: int
    active_today: bool


class XpResponse(BaseModel):
    today: int
    goal: int
    total: int


class ItemProgressResponse(BaseModel):
    item_type: str
    learning: int
    familiar: int
    mastered: int


class RecommendationResponse(BaseModel):
    target: str
    lesson_type: str | None
    title: str
    reason: str


class AchievementResponse(BaseModel):
    key: str
    title: str
    description: str
    icon: str
    unlocked_at: datetime | None


class DashboardResponse(BaseModel):
    display_name: str | None
    level: str
    streak: StreakResponse
    xp: XpResponse
    reviews_due: int
    items: list[ItemProgressResponse]
    recommendation: RecommendationResponse | None
    new_achievements: list[AchievementResponse]


class DayActivityResponse(BaseModel):
    date: date
    xp: int
    count: int
