from typing import Annotated

from fastapi import APIRouter, Depends

from english_app.core.db import SessionDep
from english_app.modules.profile.models import LearnerProfile
from english_app.modules.profile.schemas import ProfileResponse, ProfileUpdate
from english_app.modules.profile.service import ProfileService

router = APIRouter(tags=["profile"])


def get_profile_service(session: SessionDep) -> ProfileService:
    return ProfileService(session)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


@router.get("", response_model=ProfileResponse)
async def get_profile(service: ProfileServiceDep) -> LearnerProfile:
    return await service.get()


@router.put("", response_model=ProfileResponse)
async def update_profile(payload: ProfileUpdate, service: ProfileServiceDep) -> LearnerProfile:
    return await service.update(payload)
