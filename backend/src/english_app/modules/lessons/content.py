"""Structured LLM outputs for lessons and the static placement test."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class VocabularyWord(BaseModel):
    word: str
    phonetic: str
    translation: str
    mnemonic: str
    examples: list[str]


class GapExercise(BaseModel):
    sentence: str  # contains "___" where the answer goes
    accepted_answers: list[str]
    hint: str


class VocabularyLesson(BaseModel):
    topic: str
    words: list[VocabularyWord]
    exercises: list[GapExercise]


class GrammarExerciseKind(StrEnum):
    GAP = "gap"
    CORRECTION = "correction"
    TRANSFORMATION = "transformation"


class GrammarExercise(BaseModel):
    kind: GrammarExerciseKind
    instruction: str
    prompt: str
    accepted_answers: list[str]


class GrammarExample(BaseModel):
    english: str
    note: str


class GrammarLesson(BaseModel):
    topic: str
    explanation: str
    examples: list[GrammarExample]
    exercises: list[GrammarExercise]


class WritingTask(BaseModel):
    topic: str
    prompt: str
    instructions: str
    min_words: int = Field(ge=20, le=400)
    useful_phrases: list[str]


class WritingError(BaseModel):
    fragment: str
    correction: str
    explanation: str


class WritingFeedback(BaseModel):
    score: int = Field(ge=0, le=10)
    strengths: list[str]
    errors: list[WritingError]
    corrected_text: str


class AnswerCheck(BaseModel):
    correct: bool
    explanation: str


class PlacementResult(BaseModel):
    level: Literal["A1", "A2", "B1", "B2", "C1", "C2"]
    explanation: str
    next_steps: list[str]


# Placement questions from docs/SYSTEM_PROMPT.md, with the source sentences in Polish.
PLACEMENT_BANDS = {
    "basic": {
        "translation": "Wczoraj poszedłem do sklepu i kupiłem mleko.",
        "translation_expected": "Yesterday I went to the shop and bought milk.",
        "correction": "She go to school yesterday.",
        "correction_expected": "She went to school yesterday.",
    },
    "intermediate": {
        "translation": "Gdybym wiedział o spotkaniu wcześniej, przyszedłbym.",
        "translation_expected": "If I had known about the meeting earlier, I would have attended.",
        "correction": "I'm living here since 2020.",
        "correction_expected": "I've been living here since 2020.",
    },
    "advanced": {
        "translation": (
            "Mimo że przygotowała się bardzo dokładnie, w miarę zbliżania się prezentacji "
            "czuła coraz większy niepokój."
        ),
        "translation_expected": (
            "Despite having prepared thoroughly, she felt increasingly anxious as the "
            "presentation approached."
        ),
        "correction": "Having been told the news, he couldn't hardly believe it.",
        "correction_expected": "Having been told the news, he could hardly believe it.",
    },
}


def placement_band(self_level: str) -> str:
    if self_level in ("A1", "A2"):
        return "basic"
    if self_level in ("B1", "B2"):
        return "intermediate"
    return "advanced"


# Grammar topics per level band, from TEMPLATE.md.
GRAMMAR_TOPICS = {
    "basic": [
        "Present Simple (be, have, do)",
        "Articles (a, an, the)",
        "Basic prepositions (in, on, at)",
        "Past Simple",
        "Can / can't",
        "Future with 'going to'",
        "There is / there are",
    ],
    "intermediate": [
        "Present Perfect",
        "Present Perfect vs Past Simple",
        "Conditionals (types 0, 1, 2)",
        "Passive voice (basics)",
        "Relative clauses (who, which, that)",
        "Used to / would",
        "Reported speech",
        "Past Perfect",
        "Wish / if only",
    ],
    "advanced": [
        "Inversion for emphasis",
        "Mixed conditionals",
        "Cleft sentences",
        "Participle clauses",
        "Advanced passive constructions",
        "Subjunctive mood",
        "Nominalisation",
    ],
}
