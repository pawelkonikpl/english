from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.profile.models import LearnerProfile
from english_app.modules.profile.repository import ProfileRepository
from english_app.modules.profile.schemas import ProfileUpdate

NULLABLE_FIELDS = {"display_name", "target_level"}


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._profiles = ProfileRepository(session)

    async def get(self) -> LearnerProfile:
        profile = await self._profiles.get()
        if profile is None:  # first visit: persist the defaults once
            profile = LearnerProfile()
            self._profiles.save(profile)
            await self._session.commit()
        return profile

    async def update(self, data: ProfileUpdate) -> LearnerProfile:
        profile = await self._profiles.get_or_default()
        for field_name in data.model_fields_set:
            value = getattr(data, field_name)
            if value is None and field_name not in NULLABLE_FIELDS:
                continue
            setattr(profile, field_name, value)
        self._profiles.save(profile)
        await self._session.commit()
        await self._session.refresh(profile)
        return profile
