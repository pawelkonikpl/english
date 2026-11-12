from typing import Annotated

from fastapi import APIRouter, Depends, Query

from english_app.core.db import SessionDep
from english_app.core.dependencies import ClockDep, EventBusDep
from english_app.llm.service import LLMServiceDep
from english_app.modules.review.public import summary
from english_app.modules.review.schemas import (
    CardResponse,
    DueItemResponse,
    GradeRequest,
    GradeResponse,
    RecallCheckRequest,
    RecallCheckResponse,
    ReviewSummaryResponse,
    SentenceCheckRequest,
    SentenceCheckResponse,
)
from english_app.modules.review.service import ReviewService

router = APIRouter(tags=["review"])


def get_review_service(session: SessionDep, clock: ClockDep, bus: EventBusDep) -> ReviewService:
    return ReviewService(session, clock, bus)


ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


@router.get("/due", response_model=list[DueItemResponse])
async def get_due(
    service: ReviewServiceDep, limit: Annotated[int, Query(ge=1, le=200)] = 30
) -> list[DueItemResponse]:
    return [
        DueItemResponse(
            id=due.item.id or 0,
            item_type=due.item.item_type,
            item_id=due.item.item_id,
            step=due.item.step,
            mastery=due.item.mastery,
            due_on=due.item.due_on,
            lapses=due.item.lapses,
            card=CardResponse(
                front=due.card.front,
                back=due.card.back,
                example=due.card.example,
                note=due.card.note,
                label=due.card.label,
            ),
        )
        for due in await service.due_cards(limit)
    ]


@router.get("/summary", response_model=ReviewSummaryResponse)
async def get_summary(session: SessionDep, clock: ClockDep) -> ReviewSummaryResponse:
    result = await summary(session, clock.today())
    return ReviewSummaryResponse(due_today=result.due_today, total_reviews=result.total_reviews)


@router.post("/items/{review_item_id}/grade", response_model=GradeResponse)
async def grade_item(
    review_item_id: int, payload: GradeRequest, service: ReviewServiceDep, clock: ClockDep
) -> GradeResponse:
    item = await service.grade(review_item_id, payload.grade, payload.mode)
    return GradeResponse(
        id=review_item_id,
        step=item.step,
        mastery=item.mastery,
        interval_days=item.interval_days,
        due_on=item.due_on,
        due_again_today=item.due_on <= clock.today(),
    )


@router.post("/items/{review_item_id}/check-recall", response_model=RecallCheckResponse)
async def check_recall(
    review_item_id: int, payload: RecallCheckRequest, service: ReviewServiceDep
) -> RecallCheckResponse:
    correct, expected = await service.check_recall(review_item_id, payload.answer)
    return RecallCheckResponse(correct=correct, expected=expected)


@router.post("/items/{review_item_id}/check-sentence", response_model=SentenceCheckResponse)
async def check_sentence(
    review_item_id: int,
    payload: SentenceCheckRequest,
    service: ReviewServiceDep,
    llm: LLMServiceDep,
) -> SentenceCheckResponse:
    result = await service.check_sentence(review_item_id, payload.sentence, llm)
    return SentenceCheckResponse(**result.value.model_dump(), model=result.model)
