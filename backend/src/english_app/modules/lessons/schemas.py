from datetime import datetime

from pydantic import BaseModel, Field

from english_app.modules.lessons.content import (
    GrammarExample,
    VocabularyWord,
    WritingFeedback,
)
from english_app.modules.lessons.models import LessonStatus, LessonType


class CreateLessonRequest(BaseModel):
    type: LessonType
    topic: str | None = Field(default=None, max_length=300)


class AnswerFeedback(BaseModel):
    answer: str
    correct: bool
    expected: str
    explanation: str | None


class ExerciseResponse(BaseModel):
    index: int
    kind: str
    instruction: str
    prompt: str
    hint: str | None
    result: AnswerFeedback | None


class WritingTaskResponse(BaseModel):
    prompt: str
    instructions: str
    min_words: int
    useful_phrases: list[str]


class LessonResponse(BaseModel):
    id: int
    type: LessonType
    topic: str
    level: str
    status: LessonStatus
    score: int | None
    max_score: int | None
    model: str | None
    created_at: datetime
    words: list[VocabularyWord]
    explanation: str | None
    examples: list[GrammarExample]
    exercises: list[ExerciseResponse]
    writing: WritingTaskResponse | None
    writing_text: str | None
    writing_feedback: WritingFeedback | None


class LessonListItem(BaseModel):
    id: int
    type: LessonType
    topic: str
    status: LessonStatus
    score: int | None
    max_score: int | None
    created_at: datetime


class AnswerRequest(BaseModel):
    exercise_index: int = Field(ge=0)
    answer: str = Field(min_length=1, max_length=1000)


class WritingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=6000)


class PlacementQuestions(BaseModel):
    band: str
    translation_source: str
    correction_source: str


class PlacementRequest(BaseModel):
    self_level: str = Field(pattern="^(A1|A2|B1|B2|C1|C2)$")
    translation: str = Field(min_length=1, max_length=1000)
    correction: str = Field(min_length=1, max_length=1000)


class PlacementResponse(BaseModel):
    level: str
    explanation: str
    next_steps: list[str]
    model: str | None
