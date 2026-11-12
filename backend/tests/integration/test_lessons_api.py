import pytest
from httpx import AsyncClient

from english_app.modules.lessons.content import (
    AnswerCheck,
    GapExercise,
    GrammarExample,
    GrammarExercise,
    GrammarExerciseKind,
    GrammarLesson,
    PlacementResult,
    VocabularyLesson,
    VocabularyWord,
    WritingError,
    WritingFeedback,
)
from tests.support import RecordingProvider

WORDS = ["commute", "deadline", "meeting", "schedule", "colleague"]


@pytest.fixture(autouse=True)
def realistic_lessons(provider: RecordingProvider) -> None:
    provider.register(
        VocabularyLesson,
        lambda messages: VocabularyLesson(
            topic="Work vocabulary",
            words=[
                VocabularyWord(
                    word=w,
                    phonetic=f"/{w}/",
                    translation=f"pl-{w}",
                    mnemonic="skojarzenie",
                    examples=[f"Example with {w}.", f"Another {w}."],
                )
                for w in WORDS
            ],
            exercises=[
                GapExercise(
                    sentence=f"I have a ___ today ({w}).", accepted_answers=[w, f"{w}s"], hint="h"
                )
                for w in WORDS
            ],
        ),
    )
    provider.register(
        GrammarLesson,
        lambda messages: GrammarLesson(
            topic="Present Simple",
            explanation="Wyjaśnienie.",
            examples=[GrammarExample(english="She works.", note="3. osoba")],
            exercises=[
                GrammarExercise(
                    kind=GrammarExerciseKind.GAP,
                    instruction="Uzupełnij.",
                    prompt="She ___ (work) here.",
                    accepted_answers=["works"],
                ),
                GrammarExercise(
                    kind=GrammarExerciseKind.CORRECTION,
                    instruction="Popraw zdanie.",
                    prompt="He go to school.",
                    accepted_answers=["He goes to school."],
                ),
            ],
        ),
    )
    provider.register(AnswerCheck, lambda messages: AnswerCheck(correct=True, explanation="OK."))
    provider.register(
        WritingFeedback,
        lambda messages: WritingFeedback(
            score=7,
            strengths=["Jasno"],
            errors=[
                WritingError(
                    fragment="in saturday", correction="on Saturday", explanation="on + dzień"
                )
            ],
            corrected_text="I go to the cinema on Saturday.",
        ),
    )
    provider.register(
        PlacementResult,
        lambda messages: PlacementResult(level="B2", explanation="Dobrze.", next_steps=["Czytaj"]),
    )


async def create(client: AsyncClient, kind: str, topic: str | None = None) -> dict:
    response = await client.post("/api/lessons", json={"type": kind, "topic": topic})
    assert response.status_code == 201, response.text
    return response.json()


async def answer(client: AsyncClient, lesson_id: int, index: int, text: str):
    return await client.post(
        f"/api/lessons/{lesson_id}/answers", json={"exercise_index": index, "answer": text}
    )


async def test_vocabulary_lesson_flow(client: AsyncClient) -> None:
    lesson = await create(client, "vocabulary")
    lid = lesson["id"]

    await answer(client, lid, 0, "commute")  # exact word
    await answer(client, lid, 1, "I have a deadlines today (deadline).")  # whole sentence, plural
    wrong = (await answer(client, lid, 2, "party")).json()
    duplicate = await answer(client, lid, 0, "commute")
    out_of_range = await answer(client, lid, 9, "x")
    done = (await client.post(f"/api/lessons/{lid}/complete")).json()
    again = (await client.post(f"/api/lessons/{lid}/complete")).json()

    assert [w["word"] for w in lesson["words"]] == WORDS
    assert all(e["result"] is None for e in lesson["exercises"])  # answers are not leaked
    assert wrong["exercises"][2]["result"] == {
        "answer": "party",
        "correct": False,
        "expected": "meeting",
        "explanation": None,
    }
    assert duplicate.status_code == 409
    assert out_of_range.status_code == 422
    assert (done["status"], done["score"], done["max_score"]) == ("completed", 4, 10)
    assert again["score"] == 4


async def test_completed_vocabulary_words_are_reviewed_and_earn_xp(client: AsyncClient) -> None:
    lesson = await create(client, "vocabulary")
    await answer(client, lesson["id"], 0, "commute")
    await client.post(f"/api/lessons/{lesson['id']}/complete")

    due = (await client.get("/api/review/due")).json()
    dashboard = (await client.get("/api/progress/dashboard")).json()

    assert sorted(d["card"]["front"] for d in due) == sorted(WORDS)
    assert {d["card"]["label"] for d in due} == {"Słówko z lekcji"}
    assert dashboard["xp"]["today"] == 2
    assert "first_lesson" in [a["key"] for a in dashboard["new_achievements"]]


async def test_open_grammar_answer_is_checked_by_ai_on_the_fast_model(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    await client.put("/api/llm/settings", json={"main": "fake-main", "fast": "fake-fast"})
    lesson = await create(client, "grammar")

    gap = (await answer(client, lesson["id"], 0, "work")).json()
    correction = (await answer(client, lesson["id"], 1, "He is going to school.")).json()

    assert gap["exercises"][0]["result"]["correct"] is False
    assert correction["exercises"][1]["result"]["correct"] is True
    assert correction["exercises"][1]["result"]["explanation"] == "OK."
    assert provider.calls_for("AnswerCheck") == ["fake-fast"]  # only for the open exercise
    assert provider.calls_for("GrammarLesson") == ["fake-main"]


async def test_default_grammar_topics_follow_the_level_list(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    first = await create(client, "grammar")
    await client.post(f"/api/lessons/{first['id']}/complete")
    await create(client, "grammar")

    prompts = provider.systems_for("GrammarLesson")

    assert "Grammar point: Present Simple (be, have, do)" in prompts[0]  # A2 learner
    assert "Grammar point: Articles (a, an, the)" in prompts[1]


async def test_known_words_are_passed_to_the_next_lesson(
    client: AsyncClient, provider: RecordingProvider
) -> None:
    await create(client, "vocabulary")
    await create(client, "vocabulary")

    second_prompt = provider.systems_for("VocabularyLesson")[1]

    assert "commute" in second_prompt and "colleague" in second_prompt


async def test_writing_lesson_is_scored_and_awards_its_score_as_xp(client: AsyncClient) -> None:
    lesson = await create(client, "writing", topic="My weekend")
    early_complete = await client.post(f"/api/lessons/{lesson['id']}/complete")

    scored = (
        await client.post(
            f"/api/lessons/{lesson['id']}/writing", json={"text": "I go to cinema in saturday."}
        )
    ).json()
    dashboard = (await client.get("/api/progress/dashboard")).json()

    assert early_complete.status_code == 422
    assert (scored["status"], scored["score"], scored["max_score"]) == ("completed", 7, 10)
    assert scored["writing_feedback"]["errors"][0]["correction"] == "on Saturday"
    assert scored["writing_text"] == "I go to cinema in saturday."
    assert dashboard["xp"]["today"] == 7


async def test_placement_sets_the_level_without_xp_or_history(client: AsyncClient) -> None:
    questions = (await client.get("/api/lessons/placement", params={"self_level": "B2"})).json()
    result = await client.post(
        "/api/lessons/placement",
        json={
            "self_level": "B2",
            "translation": "If I had known...",
            "correction": "I've lived here",
        },
    )
    profile = (await client.get("/api/profile")).json()
    dashboard = (await client.get("/api/progress/dashboard")).json()

    assert questions["band"] == "intermediate"
    assert questions["translation_source"].startswith("Gdybym wiedział")
    assert result.json()["level"] == "B2"
    assert profile["level"] == "B2"
    assert (await client.get("/api/lessons")).json() == []
    assert dashboard["xp"]["total"] == 0


async def test_placement_type_cannot_be_created_as_a_lesson(client: AsyncClient) -> None:
    response = await client.post("/api/lessons", json={"type": "placement"})

    assert response.status_code == 422
