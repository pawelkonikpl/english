from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from english_app.core.db import SessionDep
from english_app.core.dependencies import ClockDep, EventBusDep
from english_app.llm.service import LLMServiceDep
from english_app.modules.lessons.content import (
    GrammarLesson,
    VocabularyWord,
    WritingFeedback,
    WritingTask,
)
from english_app.modules.lessons.models import LessonType
from english_app.modules.lessons.schemas import (
    AnswerFeedback,
    AnswerRequest,
    CreateLessonRequest,
    ExerciseResponse,
    LessonListItem,
    LessonResponse,
    PlacementQuestions,
    PlacementRequest,
    PlacementResponse,
    WritingRequest,
    WritingTaskResponse,
)
from english_app.modules.lessons.service import LessonService, LessonView

router = APIRouter(tags=["lessons"])


def get_lesson_service(
    session: SessionDep, clock: ClockDep, bus: EventBusDep, llm: LLMServiceDep
) -> LessonService:
    return LessonService(session, clock, bus, llm)


LessonServiceDep = Annotated[LessonService, Depends(get_lesson_service)]


def _lesson(view: LessonView) -> LessonResponse:
    lesson = view.lesson
    grammar = (
        GrammarLesson.model_validate(lesson.content) if lesson.type is LessonType.GRAMMAR else None
    )
    writing = (
        WritingTask.model_validate(lesson.content) if lesson.type is LessonType.WRITING else None
    )
    writing_answer = view.answers.get(0) if writing else None
    exercises = []
    for exercise in view.exercises:
        answer = view.answers.get(exercise.index)
        feedback = answer.feedback or {} if answer else {}
        exercises.append(
            ExerciseResponse(
                index=exercise.index,
                kind=exercise.kind,
                instruction=exercise.instruction,
                prompt=exercise.prompt,
                hint=exercise.hint,
                result=AnswerFeedback(
                    answer=answer.answer,
                    correct=answer.is_correct,
                    expected=str(feedback.get("expected", "")),
                    explanation=feedback.get("explanation"),
                )
                if answer
                else None,
            )
        )
    return LessonResponse(
        id=lesson.id or 0,
        type=lesson.type,
        topic=str(lesson.content.get("topic") or lesson.topic),
        level=lesson.level,
        status=lesson.status,
        score=lesson.score,
        max_score=lesson.max_score,
        model=lesson.model,
        created_at=lesson.created_at,
        words=[
            VocabularyWord(
                word=w.word,
                phonetic=w.phonetic or "",
                translation=w.translation,
                mnemonic=w.mnemonic or "",
                examples=w.examples,
            )
            for w in view.words
        ],
        explanation=grammar.explanation if grammar else None,
        examples=grammar.examples if grammar else [],
        exercises=exercises,
        writing=WritingTaskResponse(
            prompt=writing.prompt,
            instructions=writing.instructions,
            min_words=writing.min_words,
            useful_phrases=writing.useful_phrases,
        )
        if writing
        else None,
        writing_text=writing_answer.answer if writing_answer else None,
        writing_feedback=WritingFeedback.model_validate(writing_answer.feedback)
        if writing_answer and writing_answer.feedback
        else None,
    )


@router.get("/placement", response_model=PlacementQuestions)
async def get_placement(
    service: LessonServiceDep,
    self_level: Annotated[str, Query(pattern="^(A1|A2|B1|B2|C1|C2)$")] = "A2",
) -> PlacementQuestions:
    return PlacementQuestions(**service.placement_questions(self_level))


@router.post("/placement", response_model=PlacementResponse)
async def run_placement(payload: PlacementRequest, service: LessonServiceDep) -> PlacementResponse:
    result, model = await service.run_placement(
        payload.self_level, payload.translation, payload.correction
    )
    return PlacementResponse(**result.model_dump(), model=model)


@router.get("", response_model=list[LessonListItem])
async def list_lessons(service: LessonServiceDep) -> list[LessonListItem]:
    return [
        LessonListItem(
            id=lesson.id or 0,
            type=lesson.type,
            topic=str(lesson.content.get("topic") or lesson.topic),
            status=lesson.status,
            score=lesson.score,
            max_score=lesson.max_score,
            created_at=lesson.created_at,
        )
        for lesson in await service.history()
    ]


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson(payload: CreateLessonRequest, service: LessonServiceDep) -> LessonResponse:
    return _lesson(await service.create(payload.type, payload.topic))


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: int, service: LessonServiceDep) -> LessonResponse:
    return _lesson(await service.view(lesson_id))


@router.post("/{lesson_id}/answers", response_model=LessonResponse)
async def answer_exercise(
    lesson_id: int, payload: AnswerRequest, service: LessonServiceDep
) -> LessonResponse:
    await service.answer(lesson_id, payload.exercise_index, payload.answer.strip())
    return _lesson(await service.view(lesson_id))


@router.post("/{lesson_id}/writing", response_model=LessonResponse)
async def submit_writing(
    lesson_id: int, payload: WritingRequest, service: LessonServiceDep
) -> LessonResponse:
    return _lesson(await service.submit_writing(lesson_id, payload.text.strip()))


@router.post("/{lesson_id}/complete", response_model=LessonResponse)
async def complete_lesson(lesson_id: int, service: LessonServiceDep) -> LessonResponse:
    return _lesson(await service.complete(lesson_id))
