from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from english_app.modules.conversation.models import ConversationStatus


# --- structured LLM outputs ------------------------------------------------
class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str


class TurnReply(BaseModel):
    reply: str
    corrections: list[Correction]
    better_alternatives: list[str]
    used_target_phrases: list[str]


class HintLevel(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    ADVANCED = "advanced"


class Hint(BaseModel):
    level: HintLevel
    text: str
    translation: str


class HintList(BaseModel):
    suggestions: list[Hint]


class SuggestedPhrase(BaseModel):
    english: str
    polish: str


class ConversationSummary(BaseModel):
    score: int = Field(ge=0, le=10)
    strengths: list[str]
    mistakes: list[Correction]
    new_phrases: list[SuggestedPhrase]


# --- API ------------------------------------------------------------------
class ScenarioResponse(BaseModel):
    key: str
    title: str
    emoji: str
    description: str


class StartConversationRequest(BaseModel):
    scenario_key: str
    topic: str | None = Field(default=None, max_length=300)
    target_phrase_ids: list[int] = Field(default_factory=list, max_length=30)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    feedback: dict[str, Any] | None
    model: str | None
    created_at: datetime


class TargetPhraseResponse(BaseModel):
    id: int
    english: str
    polish: str


class ConversationResponse(BaseModel):
    id: int
    scenario_key: str
    title: str
    emoji: str
    topic: str | None
    level: str
    status: ConversationStatus
    score: int | None
    summary: ConversationSummary | None
    target_phrases: list[TargetPhraseResponse]
    messages: list[MessageResponse]
    started_at: datetime


class ConversationListItem(BaseModel):
    id: int
    title: str
    emoji: str
    status: ConversationStatus
    score: int | None
    messages: int
    started_at: datetime


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse


class AddPhraseRequest(BaseModel):
    english: str = Field(min_length=1, max_length=500)
    polish: str = Field(min_length=1, max_length=500)


class AddPhraseResponse(BaseModel):
    phrase_id: int
    newly_enrolled: bool
