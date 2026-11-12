from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.errors import ConflictError, InvalidInputError, NotFoundError
from english_app.core.events import ActivityKind, EventBus, LearningActivity
from english_app.core.prompts import PromptRenderer
from english_app.core.text_matching import is_correct
from english_app.llm.base import ChatMessage, ModelTier
from english_app.llm.service import LLMService
from english_app.modules.lessons.content import (
    GRAMMAR_TOPICS,
    PLACEMENT_BANDS,
    AnswerCheck,
    GrammarExerciseKind,
    GrammarLesson,
    PlacementResult,
    VocabularyLesson,
    WritingFeedback,
    WritingTask,
    placement_band,
)
from english_app.modules.lessons.models import (
    WORD_ITEM_TYPE,
    Lesson,
    LessonAnswer,
    LessonStatus,
    LessonType,
    LessonWord,
)
from english_app.modules.lessons.repository import LessonRepository
from english_app.modules.profile.models import CefrLevel
from english_app.modules.profile.public import get_learner_context, level_guidance, set_level
from english_app.modules.review import public as review

PROMPTS = PromptRenderer(Path(__file__).parent / "prompts")
POINTS_PER_ANSWER = 2
WRITING_MAX_SCORE = 10
KNOWN_WORDS_LIMIT = 20
HISTORY_LIMIT = 30
GAP = "___"

VOCABULARY_TOPICS = [
    "Daily routine",
    "Work and online meetings",
    "Travel and airports",
    "Food and restaurants",
    "Feelings and emotions",
    "Health and the doctor",
    "Shopping and money",
    "Free time and hobbies",
    "Home and neighbours",
    "Weather and small talk",
]
WRITING_TOPICS = [
    "Your typical weekend",
    "A short message to a colleague about a delay",
    "Your last holiday",
    "Your plans for the next year",
    "A problem you solved recently",
    "Your favourite place in your city",
]
OPEN_GRAMMAR_KINDS = {GrammarExerciseKind.CORRECTION, GrammarExerciseKind.TRANSFORMATION}
LESSON_SCHEMAS: dict[LessonType, type[BaseModel]] = {
    LessonType.VOCABULARY: VocabularyLesson,
    LessonType.GRAMMAR: GrammarLesson,
    LessonType.WRITING: WritingTask,
}


class LessonNotFoundError(NotFoundError):
    def __init__(self, lesson_id: int) -> None:
        super().__init__(f"Lesson {lesson_id} not found", user_message="Nie znaleziono lekcji.")


@dataclass(frozen=True)
class Exercise:
    index: int
    kind: str
    instruction: str
    prompt: str
    hint: str | None
    accepted: list[str]


@dataclass(frozen=True)
class LessonView:
    lesson: Lesson
    exercises: list[Exercise]
    answers: dict[int, LessonAnswer]
    words: list[LessonWord]


def exercises_of(lesson: Lesson) -> list[Exercise]:
    if lesson.type is LessonType.VOCABULARY:
        vocabulary = VocabularyLesson.model_validate(lesson.content)
        return [
            Exercise(i, "gap", "Uzupełnij lukę.", e.sentence, e.hint, e.accepted_answers)
            for i, e in enumerate(vocabulary.exercises)
        ]
    if lesson.type is LessonType.GRAMMAR:
        grammar = GrammarLesson.model_validate(lesson.content)
        return [
            Exercise(i, e.kind.value, e.instruction, e.prompt, None, e.accepted_answers)
            for i, e in enumerate(grammar.exercises)
        ]
    return []


def matches_any(exercise: Exercise, answer: str) -> bool:
    for accepted in exercise.accepted:
        if is_correct(accepted, answer):
            return True
        # The learner may type the whole sentence instead of the missing word.
        if GAP in exercise.prompt and is_correct(exercise.prompt.replace(GAP, accepted), answer):
            return True
    return False


class LessonService:
    def __init__(
        self, session: AsyncSession, clock: Clock, bus: EventBus, llm: LLMService | None = None
    ) -> None:
        self._session = session
        self._clock = clock
        self._bus = bus
        self._llm = llm
        self._lessons = LessonRepository(session)

    async def create(self, lesson_type: LessonType, topic: str | None) -> LessonView:
        if lesson_type is LessonType.PLACEMENT:
            raise InvalidInputError(
                "Placement is not created through create()",
                user_message="Test poziomujący ma osobny ekran.",
            )
        learner = await get_learner_context(self._session)
        chosen_topic = (topic or "").strip() or await self._default_topic(
            lesson_type, learner.level
        )
        context: dict[str, Any] = {
            "level": learner.level.value,
            "native_language": learner.native_language_name,
            "level_rules": level_guidance(learner.level),
            "goals": learner.goals,
            "known_words": await self._lessons.recent_words(KNOWN_WORDS_LIMIT),
            "topic": chosen_topic,
        }
        schema = LESSON_SCHEMAS[lesson_type]
        result = await self._require_llm().complete_structured(
            system=PROMPTS.render(f"{_template(lesson_type)}.md", **context),
            messages=[ChatMessage(role="user", content=f"Prepare the lesson: {chosen_topic}")],
            schema=schema,
            tier=ModelTier.MAIN,
        )
        lesson = Lesson(
            type=lesson_type,
            topic=chosen_topic,
            level=learner.level.value,
            content=result.value.model_dump(),
            model=result.model,
            created_at=self._clock.now(),
        )
        self._lessons.add(lesson)
        await self._session.flush()
        if isinstance(result.value, VocabularyLesson):
            for word in result.value.words:
                self._lessons.add(
                    LessonWord(
                        lesson_id=lesson.id or 0,
                        word=word.word,
                        phonetic=word.phonetic,
                        translation=word.translation,
                        mnemonic=word.mnemonic,
                        examples=word.examples,
                    )
                )
        await self._session.commit()
        return await self.view(lesson.id or 0)

    async def view(self, lesson_id: int) -> LessonView:
        lesson = await self._get(lesson_id)
        return LessonView(
            lesson=lesson,
            exercises=exercises_of(lesson),
            answers={a.exercise_index: a for a in await self._lessons.answers(lesson_id)},
            words=await self._lessons.words(lesson_id),
        )

    async def history(self) -> list[Lesson]:
        return await self._lessons.recent(HISTORY_LIMIT, exclude=LessonType.PLACEMENT)

    async def answer(self, lesson_id: int, index: int, answer: str) -> LessonAnswer:
        lesson = await self._get(lesson_id)
        exercises = exercises_of(lesson)
        if index >= len(exercises):
            raise InvalidInputError(
                f"Lesson {lesson_id} has no exercise {index}",
                user_message="Nie ma takiego ćwiczenia.",
            )
        if any(a.exercise_index == index for a in await self._lessons.answers(lesson_id)):
            raise ConflictError(
                f"Exercise {index} of lesson {lesson_id} already answered",
                user_message="To ćwiczenie ma już odpowiedź.",
            )
        exercise = exercises[index]
        correct = matches_any(exercise, answer)
        explanation: str | None = None
        if not correct and exercise.kind in OPEN_GRAMMAR_KINDS:
            check = await self._check_open_answer(exercise, answer)
            correct, explanation = check.correct, check.explanation
        saved = LessonAnswer(
            lesson_id=lesson_id,
            exercise_index=index,
            answer=answer,
            is_correct=correct,
            feedback={"expected": exercise.accepted[0], "explanation": explanation},
            created_at=self._clock.now(),
        )
        self._lessons.add(saved)
        await self._bus.publish(
            LearningActivity(
                kind=ActivityKind.LESSON_ANSWERED,
                ref_type="lesson",
                ref_id=lesson_id,
                details={"correct": correct, "type": lesson.type.value, "index": index},
            ),
            self._session,
        )
        await self._session.commit()
        return saved

    async def submit_writing(self, lesson_id: int, text: str) -> LessonView:
        lesson = await self._get(lesson_id)
        if lesson.type is not LessonType.WRITING:
            raise InvalidInputError(
                f"Lesson {lesson_id} is not a writing lesson",
                user_message="To nie jest lekcja pisania.",
            )
        if lesson.status is LessonStatus.COMPLETED:
            return await self.view(lesson_id)
        task = WritingTask.model_validate(lesson.content)
        learner = await get_learner_context(self._session)
        result = await self._require_llm().complete_structured(
            system=PROMPTS.render(
                "writing_feedback.md",
                level=learner.level.value,
                native_language=learner.native_language_name,
                task=task.prompt,
            ),
            messages=[ChatMessage(role="user", content=text)],
            schema=WritingFeedback,
            tier=ModelTier.MAIN,
        )
        self._lessons.add(
            LessonAnswer(
                lesson_id=lesson_id,
                exercise_index=0,
                answer=text,
                is_correct=result.value.score >= WRITING_MAX_SCORE // 2,
                feedback=result.value.model_dump(),
                created_at=self._clock.now(),
            )
        )
        await self._finish(lesson, score=result.value.score, max_score=WRITING_MAX_SCORE)
        await self._session.commit()
        return await self.view(lesson_id)

    async def complete(self, lesson_id: int) -> LessonView:
        view = await self.view(lesson_id)
        lesson = view.lesson
        if lesson.status is LessonStatus.COMPLETED:
            return view
        if lesson.type is LessonType.WRITING:
            raise InvalidInputError(
                f"Writing lesson {lesson_id} completes on submission",
                user_message="Wyślij tekst, żeby zakończyć lekcję pisania.",
            )
        correct = sum(1 for a in view.answers.values() if a.is_correct)
        for word in view.words:
            await review.enroll(
                self._session, self._clock, WORD_ITEM_TYPE, word.id or 0, known=False
            )
        await self._finish(
            lesson,
            score=correct * POINTS_PER_ANSWER,
            max_score=len(view.exercises) * POINTS_PER_ANSWER,
        )
        await self._session.commit()
        return await self.view(lesson_id)

    def placement_questions(self, self_level: str) -> dict[str, str]:
        band = placement_band(self_level)
        questions = PLACEMENT_BANDS[band]
        return {
            "band": band,
            "translation_source": questions["translation"],
            "correction_source": questions["correction"],
        }

    async def run_placement(
        self, self_level: str, translation: str, correction: str
    ) -> tuple[PlacementResult, str | None]:
        questions = PLACEMENT_BANDS[placement_band(self_level)]
        learner = await get_learner_context(self._session)
        result = await self._require_llm().complete_structured(
            system=PROMPTS.render(
                "placement.md",
                native_language=learner.native_language_name,
                self_level=self_level,
                translation_source=questions["translation"],
                translation_expected=questions["translation_expected"],
                correction_source=questions["correction"],
                correction_expected=questions["correction_expected"],
            ),
            messages=[
                ChatMessage(
                    role="user",
                    content=f"Task 1 answer: {translation}\nTask 2 answer: {correction}",
                )
            ],
            schema=PlacementResult,
            tier=ModelTier.MAIN,
        )
        await set_level(self._session, CefrLevel(result.value.level))
        self._lessons.add(
            Lesson(
                type=LessonType.PLACEMENT,
                topic="Test poziomujący",
                level=result.value.level,
                content={
                    "self_level": self_level,
                    "answers": {"translation": translation, "correction": correction},
                    "result": result.value.model_dump(),
                },
                status=LessonStatus.COMPLETED,
                model=result.model,
                created_at=self._clock.now(),
                completed_at=self._clock.now(),
            )
        )
        await self._session.commit()
        return result.value, result.model

    async def _finish(self, lesson: Lesson, *, score: int, max_score: int) -> None:
        lesson.status = LessonStatus.COMPLETED
        lesson.score = score
        lesson.max_score = max_score
        lesson.completed_at = self._clock.now()
        self._lessons.add(lesson)
        details: dict[str, Any] = {
            "type": lesson.type.value,
            "score": score,
            "max_score": max_score,
        }
        if lesson.type is LessonType.WRITING:
            details["bonus_xp"] = score
        await self._bus.publish(
            LearningActivity(
                kind=ActivityKind.LESSON_COMPLETED,
                ref_type="lesson",
                ref_id=lesson.id or 0,
                details=details,
            ),
            self._session,
        )

    async def _check_open_answer(self, exercise: Exercise, answer: str) -> AnswerCheck:
        learner = await get_learner_context(self._session)
        result = await self._require_llm().complete_structured(
            system=PROMPTS.render(
                "answer_check.md",
                level=learner.level.value,
                native_language=learner.native_language_name,
                instruction=exercise.instruction,
                prompt=exercise.prompt,
                accepted=exercise.accepted,
            ),
            messages=[ChatMessage(role="user", content=answer)],
            schema=AnswerCheck,
            tier=ModelTier.FAST,
        )
        return result.value

    async def _default_topic(self, lesson_type: LessonType, level: CefrLevel) -> str:
        done = await self._lessons.topics(lesson_type)
        if lesson_type is LessonType.GRAMMAR:
            options = GRAMMAR_TOPICS[placement_band(level.value)]
        elif lesson_type is LessonType.WRITING:
            options = WRITING_TOPICS
        else:
            options = VOCABULARY_TOPICS
        return next(
            (topic for topic in options if topic not in done), options[len(done) % len(options)]
        )

    async def _get(self, lesson_id: int) -> Lesson:
        lesson = await self._lessons.get(lesson_id)
        if lesson is None:
            raise LessonNotFoundError(lesson_id)
        return lesson

    def _require_llm(self) -> LLMService:
        if self._llm is None:
            raise RuntimeError("LessonService was created without an LLM service")
        return self._llm


def _template(lesson_type: LessonType) -> str:
    return "writing_task" if lesson_type is LessonType.WRITING else lesson_type.value
