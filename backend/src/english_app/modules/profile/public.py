"""Public API of the profile module, used by other modules.

Other modules may import only from this file (and `models.CefrLevel`).
"""

from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.profile.models import CefrLevel
from english_app.modules.profile.repository import ProfileRepository

LANGUAGE_NAMES = {"pl": "Polish", "en": "English", "de": "German", "uk": "Ukrainian"}


@dataclass(frozen=True)
class LearnerContext:
    """What prompts need to know about the learner."""

    level: CefrLevel
    native_language: str
    native_language_name: str
    display_name: str | None
    daily_goal_xp: int


async def get_learner_context(session: AsyncSession) -> LearnerContext:
    profile = await ProfileRepository(session).get_or_default()
    return LearnerContext(
        level=profile.level,
        native_language=profile.native_language,
        native_language_name=LANGUAGE_NAMES.get(profile.native_language, profile.native_language),
        display_name=profile.display_name,
        daily_goal_xp=profile.daily_goal_xp,
    )


async def set_level(session: AsyncSession, level: CefrLevel) -> None:
    """Store a level determined elsewhere (e.g. the placement test). Does not commit."""
    repository = ProfileRepository(session)
    profile = await repository.get_or_default()
    profile.level = level
    repository.save(profile)


__all__ = ["CefrLevel", "LearnerContext", "get_learner_context", "set_level"]
