from typing import Annotated

from fastapi import APIRouter, Depends

from english_app.core.db import SessionDep
from english_app.core.dependencies import ClockDep, EventBusDep, SettingsDep
from english_app.llm.service import LLMServiceDep
from english_app.modules.phrases.schemas import (
    EnrollRequest,
    EnrollResponse,
    ExplainRequest,
    LearnSessionResponse,
    PhraseExplanationResponse,
    PhraseResponse,
    PhraseStatus,
    SectionResponse,
)
from english_app.modules.phrases.service import PhraseService, PhraseWithState

router = APIRouter(tags=["phrases"])


def get_phrase_service(
    session: SessionDep, clock: ClockDep, bus: EventBusDep, settings: SettingsDep
) -> PhraseService:
    return PhraseService(session, clock, bus, settings.daily_new_phrases)


PhraseServiceDep = Annotated[PhraseService, Depends(get_phrase_service)]


def to_response(item: PhraseWithState) -> PhraseResponse:
    phrase = item.phrase
    return PhraseResponse(
        id=phrase.id or 0,
        tier=phrase.tier,
        section_code=phrase.section_code,
        section_title=phrase.section_title,
        english=phrase.english,
        polish=phrase.polish,
        example=phrase.example,
        note=phrase.note,
        kind=phrase.kind,
        source=phrase.source,
        status=item.status,
        mastery=item.state.mastery if item.state else 0,
        due_on=item.state.due_on if item.state else None,
        has_explanation=phrase.ai_explanation is not None,
    )


@router.get("/sections", response_model=list[SectionResponse])
async def get_sections(service: PhraseServiceDep) -> list[SectionResponse]:
    return [
        SectionResponse(
            tier=s.tier,
            tier_title=s.tier_title,
            code=s.code,
            title=s.title,
            total=s.total,
            learning=s.learning,
            mastered=s.mastered,
        )
        for s in await service.sections()
    ]


@router.get("", response_model=list[PhraseResponse])
async def get_phrases(
    service: PhraseServiceDep, section: str | None = None, status: PhraseStatus | None = None
) -> list[PhraseResponse]:
    return [to_response(item) for item in await service.list_phrases(section, status)]


@router.get("/learn-session", response_model=LearnSessionResponse)
async def get_learn_session(service: PhraseServiceDep) -> LearnSessionResponse:
    session = await service.learn_session()
    return LearnSessionResponse(
        daily_limit=session.daily_limit,
        remaining_today=session.remaining_today,
        phrases=[to_response(item) for item in session.phrases],
    )


@router.post("/{phrase_id}/enroll", response_model=EnrollResponse)
async def enroll_phrase(
    phrase_id: int, payload: EnrollRequest, service: PhraseServiceDep
) -> EnrollResponse:
    item, review_item_id, created = await service.enroll(phrase_id, known=payload.known)
    return EnrollResponse(
        phrase_id=phrase_id,
        review_item_id=review_item_id,
        newly_enrolled=created,
        status=item.status,
    )


@router.post("/{phrase_id}/explain", response_model=PhraseExplanationResponse)
async def explain_phrase(
    phrase_id: int, payload: ExplainRequest, service: PhraseServiceDep, llm: LLMServiceDep
) -> PhraseExplanationResponse:
    explanation, model, cached = await service.explain(
        phrase_id, llm, regenerate=payload.regenerate
    )
    return PhraseExplanationResponse(**explanation.model_dump(), model=model, cached=cached)
