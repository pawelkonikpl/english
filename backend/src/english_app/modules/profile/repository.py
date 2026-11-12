from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.profile.models import PROFILE_ID, LearnerProfile, utc_now


class ProfileRepository:
    """Single-row learner profile. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> LearnerProfile | None:
        return await self._session.get(LearnerProfile, PROFILE_ID)

    async def get_or_default(self) -> LearnerProfile:
        profile = await self.get()
        return profile if profile is not None else LearnerProfile()

    def save(self, profile: LearnerProfile) -> None:
        profile.updated_at = utc_now()
        self._session.add(profile)
