from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.errors import ConflictError, InvalidInputError, NotFoundError
from english_app.core.events import ActivityKind, EventBus, LearningActivity
from english_app.core.prompts import PromptRenderer
from english_app.llm.base import ChatMessage, ModelTier
from english_app.llm.service import LLMService
from english_app.modules.conversation.models import (
    Conversation,
    ConversationMessage,
    ConversationStatus,
)
from english_app.modules.conversation.repository import ConversationRepository
from english_app.modules.conversation.scenarios import Scenario, find_scenario
from english_app.modules.conversation.schemas import (
    ConversationSummary,
    HintList,
    TurnReply,
)
from english_app.modules.phrases import public as phrases
from english_app.modules.profile.public import get_learner_context, level_guidance

PROMPTS = PromptRenderer(Path(__file__).parent / "prompts")
OPENING_TRIGGER = "(The learner is ready. Begin the role-play.)"
RECENT_LIMIT = 20


class ConversationNotFoundError(NotFoundError):
    def __init__(self, conversation_id: int) -> None:
        super().__init__(
            f"Conversation {conversation_id} not found", user_message="Nie znaleziono rozmowy."
        )


class UnknownScenarioError(InvalidInputError):
    def __init__(self, key: str) -> None:
        super().__init__(f"Unknown scenario {key!r}", user_message="Nieznana scenka.")


class ConversationFinishedError(ConflictError):
    def __init__(self, conversation_id: int) -> None:
        super().__init__(
            f"Conversation {conversation_id} is finished",
            user_message="Ta rozmowa jest już zakończona. Zacznij nową.",
        )


@dataclass(frozen=True)
class ConversationView:
    conversation: Conversation
    scenario: Scenario
    messages: list[ConversationMessage]
    target_phrases: list[phrases.PhraseText]


class ConversationService:
    def __init__(
        self, session: AsyncSession, clock: Clock, bus: EventBus, llm: LLMService | None = None
    ) -> None:
        self._session = session
        self._clock = clock
        self._bus = bus
        self._llm = llm
        self._conversations = ConversationRepository(session)

    async def start(
        self, scenario_key: str, topic: str | None, target_phrase_ids: list[int]
    ) -> ConversationView:
        scenario = find_scenario(scenario_key)
        if scenario is None:
            raise UnknownScenarioError(scenario_key)
        learner = await get_learner_context(self._session)
        targets = await phrases.get_phrase_texts(self._session, target_phrase_ids)
        conversation = Conversation(
            scenario_key=scenario.key,
            title=scenario.title,
            topic=(topic or "").strip() or None,
            level=learner.level.value,
            target_phrase_ids=[t.id for t in targets],
            started_at=self._clock.now(),
        )
        system = await self._system_prompt("turn.md", conversation, scenario, structured=False)
        opening = await self._require_llm().complete(
            system=system,
            messages=[ChatMessage(role="user", content=OPENING_TRIGGER)],
            tier=ModelTier.MAIN,
        )
        self._conversations.add(conversation)
        await self._session.flush()
        self._conversations.add(
            ConversationMessage(
                conversation_id=conversation.id or 0,
                role="assistant",
                content=opening.value.strip(),
                model=opening.model,
                created_at=self._clock.now(),
            )
        )
        await self._session.commit()
        return await self.view(conversation.id or 0)

    async def view(self, conversation_id: int) -> ConversationView:
        conversation = await self._get(conversation_id)
        return ConversationView(
            conversation=conversation,
            scenario=self._scenario(conversation),
            messages=await self._conversations.messages(conversation_id),
            target_phrases=await phrases.get_phrase_texts(
                self._session, conversation.target_phrase_ids
            ),
        )

    async def recent(self) -> list[tuple[Conversation, Scenario, int]]:
        return [
            (conversation, self._scenario(conversation), count)
            for conversation, count in await self._conversations.recent(RECENT_LIMIT)
        ]

    async def send(
        self, conversation_id: int, content: str
    ) -> tuple[ConversationMessage, ConversationMessage]:
        conversation = await self._get_active(conversation_id)
        scenario = self._scenario(conversation)
        history = await self._conversations.messages(conversation_id)
        system = await self._system_prompt("turn.md", conversation, scenario, structured=True)
        result = await self._require_llm().complete_structured(
            system=system,
            messages=[*_as_chat(history), ChatMessage(role="user", content=content)],
            schema=TurnReply,
            tier=ModelTier.MAIN,
        )
        # Messages are stored only after the model answered, so a failed call leaves no trace.
        user_message = ConversationMessage(
            conversation_id=conversation_id,
            role="user",
            content=content,
            feedback={
                "corrections": [c.model_dump() for c in result.value.corrections],
                "better_alternatives": result.value.better_alternatives,
                "used_target_phrases": result.value.used_target_phrases,
            },
            created_at=self._clock.now(),
        )
        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=result.value.reply.strip(),
            model=result.model,
            created_at=self._clock.now(),
        )
        self._conversations.add(user_message)
        self._conversations.add(assistant_message)
        await self._session.commit()
        return user_message, assistant_message

    async def hint(self, conversation_id: int) -> HintList:
        conversation = await self._get_active(conversation_id)
        history = await self._conversations.messages(conversation_id)
        system = await self._system_prompt("hint.md", conversation, self._scenario(conversation))
        result = await self._require_llm().complete_structured(
            system=system,
            messages=[
                *_as_chat(history),
                ChatMessage(role="user", content="(Suggest my next reply.)"),
            ],
            schema=HintList,
            tier=ModelTier.FAST,
        )
        return result.value

    async def finish(self, conversation_id: int) -> ConversationView:
        conversation = await self._get(conversation_id)
        if conversation.status is ConversationStatus.FINISHED:
            return await self.view(conversation_id)
        history = await self._conversations.messages(conversation_id)
        if not any(m.role == "user" for m in history):
            raise InvalidInputError(
                f"Conversation {conversation_id} has no learner messages",
                user_message="Napisz chociaż jedną wiadomość, zanim zakończysz rozmowę.",
            )
        system = await self._system_prompt("summary.md", conversation, self._scenario(conversation))
        result = await self._require_llm().complete_structured(
            system=system,
            messages=[ChatMessage(role="user", content=_transcript(history))],
            schema=ConversationSummary,
            tier=ModelTier.MAIN,
        )
        conversation.status = ConversationStatus.FINISHED
        conversation.score = result.value.score
        conversation.summary = result.value.model_dump()
        conversation.summary_model = result.model
        conversation.finished_at = self._clock.now()
        self._conversations.add(conversation)
        await self._bus.publish(
            LearningActivity(
                kind=ActivityKind.CONVERSATION_FINISHED,
                ref_type="conversation",
                ref_id=conversation_id,
                details={"score": result.value.score, "scenario": conversation.scenario_key},
            ),
            self._session,
        )
        await self._session.commit()
        return await self.view(conversation_id)

    async def add_phrase(self, conversation_id: int, english: str, polish: str) -> tuple[int, bool]:
        conversation = await self._get(conversation_id)
        phrase_id, created = await phrases.add_ai_phrase(
            self._session,
            self._clock,
            self._bus,
            english=english,
            polish=polish,
            note=f"Z rozmowy: {conversation.title}",
        )
        await self._session.commit()
        return phrase_id, created

    async def _system_prompt(
        self,
        template: str,
        conversation: Conversation,
        scenario: Scenario,
        *,
        structured: bool = True,
    ) -> str:
        learner = await get_learner_context(self._session)
        targets = await phrases.get_phrase_texts(self._session, conversation.target_phrase_ids)
        context: dict[str, Any] = {
            "scenario": scenario,
            "topic": conversation.topic,
            "level": conversation.level,
            "native_language": learner.native_language_name,
            "level_rules": level_guidance(learner.level),
            "target_phrases": [f"{t.english} ({t.polish})" for t in targets],
            "structured": structured,
        }
        return PROMPTS.render(template, **context)

    async def _get(self, conversation_id: int) -> Conversation:
        conversation = await self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    async def _get_active(self, conversation_id: int) -> Conversation:
        conversation = await self._get(conversation_id)
        if conversation.status is ConversationStatus.FINISHED:
            raise ConversationFinishedError(conversation_id)
        return conversation

    def _scenario(self, conversation: Conversation) -> Scenario:
        scenario = find_scenario(conversation.scenario_key)
        if scenario is None:
            raise UnknownScenarioError(conversation.scenario_key)
        return scenario

    def _require_llm(self) -> LLMService:
        if self._llm is None:
            raise RuntimeError("ConversationService was created without an LLM service")
        return self._llm


def _as_chat(messages: list[ConversationMessage]) -> list[ChatMessage]:
    return [
        ChatMessage(role="user" if m.role == "user" else "assistant", content=m.content)
        for m in messages
    ]


def _transcript(messages: list[ConversationMessage]) -> str:
    lines = [f"{'User' if m.role == 'user' else 'Partner'}: {m.content}" for m in messages]
    return "Conversation transcript:\n\n" + "\n".join(lines)
