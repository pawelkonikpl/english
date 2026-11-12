from typing import Annotated

from fastapi import APIRouter, Depends, status

from english_app.core.db import SessionDep
from english_app.core.dependencies import ClockDep, EventBusDep
from english_app.llm.service import LLMServiceDep
from english_app.modules.conversation.models import ConversationMessage
from english_app.modules.conversation.scenarios import all_scenarios
from english_app.modules.conversation.schemas import (
    AddPhraseRequest,
    AddPhraseResponse,
    ConversationListItem,
    ConversationResponse,
    ConversationSummary,
    HintList,
    MessageResponse,
    ScenarioResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartConversationRequest,
    TargetPhraseResponse,
)
from english_app.modules.conversation.service import ConversationService, ConversationView

router = APIRouter(tags=["conversation"])


def get_conversation_service(
    session: SessionDep, clock: ClockDep, bus: EventBusDep, llm: LLMServiceDep
) -> ConversationService:
    return ConversationService(session, clock, bus, llm)


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]


def _message(message: ConversationMessage) -> MessageResponse:
    return MessageResponse(
        id=message.id or 0,
        role=message.role,
        content=message.content,
        feedback=message.feedback,
        model=message.model,
        created_at=message.created_at,
    )


def _conversation(view: ConversationView) -> ConversationResponse:
    c = view.conversation
    return ConversationResponse(
        id=c.id or 0,
        scenario_key=c.scenario_key,
        title=c.title,
        emoji=view.scenario.emoji,
        topic=c.topic,
        level=c.level,
        status=c.status,
        score=c.score,
        summary=ConversationSummary.model_validate(c.summary) if c.summary else None,
        target_phrases=[
            TargetPhraseResponse(id=t.id, english=t.english, polish=t.polish)
            for t in view.target_phrases
        ],
        messages=[_message(m) for m in view.messages],
        started_at=c.started_at,
    )


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def get_scenarios() -> list[ScenarioResponse]:
    return [
        ScenarioResponse(key=s.key, title=s.title, emoji=s.emoji, description=s.description)
        for s in all_scenarios()
    ]


@router.get("", response_model=list[ConversationListItem])
async def list_conversations(service: ConversationServiceDep) -> list[ConversationListItem]:
    return [
        ConversationListItem(
            id=c.id or 0,
            title=c.title,
            emoji=scenario.emoji,
            status=c.status,
            score=c.score,
            messages=count,
            started_at=c.started_at,
        )
        for c, scenario, count in await service.recent()
    ]


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    payload: StartConversationRequest, service: ConversationServiceDep
) -> ConversationResponse:
    view = await service.start(payload.scenario_key, payload.topic, payload.target_phrase_ids)
    return _conversation(view)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int, service: ConversationServiceDep
) -> ConversationResponse:
    return _conversation(await service.view(conversation_id))


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: int, payload: SendMessageRequest, service: ConversationServiceDep
) -> SendMessageResponse:
    user_message, assistant_message = await service.send(conversation_id, payload.content.strip())
    return SendMessageResponse(
        user_message=_message(user_message), assistant_message=_message(assistant_message)
    )


@router.post("/{conversation_id}/hint", response_model=HintList)
async def get_hint(conversation_id: int, service: ConversationServiceDep) -> HintList:
    return await service.hint(conversation_id)


@router.post("/{conversation_id}/finish", response_model=ConversationResponse)
async def finish_conversation(
    conversation_id: int, service: ConversationServiceDep
) -> ConversationResponse:
    return _conversation(await service.finish(conversation_id))


@router.post("/{conversation_id}/phrases", response_model=AddPhraseResponse)
async def add_phrase(
    conversation_id: int, payload: AddPhraseRequest, service: ConversationServiceDep
) -> AddPhraseResponse:
    phrase_id, created = await service.add_phrase(conversation_id, payload.english, payload.polish)
    return AddPhraseResponse(phrase_id=phrase_id, newly_enrolled=created)
