from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from english_app.modules.profile.models import CefrLevel


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None
    level: CefrLevel
    target_level: CefrLevel | None
    native_language: str
    goals: list[str]
    daily_goal_xp: int
    onboarding_done: bool
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Partial update: fields left out stay unchanged."""

    display_name: str | None = Field(default=None, max_length=100)
    level: CefrLevel | None = None
    target_level: CefrLevel | None = None
    native_language: str | None = Field(default=None, min_length=2, max_length=10)
    goals: list[str] | None = None
    daily_goal_xp: int | None = Field(default=None, ge=5, le=500)
    onboarding_done: bool | None = None
