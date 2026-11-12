from datetime import date, timedelta

import pytest

from english_app.core.events import ActivityKind, LearningActivity
from english_app.modules.progress.rules import (
    RecommendationInput,
    compute_streak,
    plural_pl,
    points_for,
    recommend,
)

TODAY = date(2026, 11, 12)
ALL_MODULES = frozenset({"review", "phrases", "lessons", "conversation"})


def activity(kind: ActivityKind, **details: object) -> LearningActivity:
    return LearningActivity(kind=kind, ref_type="x", ref_id=1, details=dict(details))


@pytest.mark.parametrize(
    ("item", "points"),
    [
        (activity(ActivityKind.REVIEW_GRADED, grade="good"), 1.0),
        (activity(ActivityKind.REVIEW_GRADED, grade="easy"), 1.0),
        (activity(ActivityKind.REVIEW_GRADED, grade="hard"), 0.5),
        (activity(ActivityKind.REVIEW_GRADED, grade="again"), 0.0),
        (activity(ActivityKind.PHRASE_ENROLLED), 1.0),
        (activity(ActivityKind.LESSON_ANSWERED, correct=True), 2.0),
        (activity(ActivityKind.LESSON_ANSWERED, correct=False), 0.0),
        (activity(ActivityKind.CONVERSATION_FINISHED, score=7), 7.0),
        (activity(ActivityKind.CONVERSATION_FINISHED, score=99), 10.0),
        (activity(ActivityKind.LESSON_COMPLETED, type="grammar"), 0.0),
        (activity(ActivityKind.LESSON_COMPLETED, type="writing", bonus_xp=6), 6.0),
        (activity(ActivityKind.MILESTONE_REACHED, milestone="phrases_tier_1"), 0.0),
    ],
)
def test_points_per_activity(item: LearningActivity, points: float) -> None:
    assert points_for(item) == points


def days_ago(*offsets: int) -> list[date]:
    return [TODAY - timedelta(days=n) for n in offsets]


@pytest.mark.parametrize(
    ("active", "current", "longest", "active_today"),
    [
        ([], 0, 0, False),
        (days_ago(0), 1, 1, True),
        (days_ago(1, 2, 3), 3, 3, False),  # today not over yet: the streak still counts
        (days_ago(0, 1, 3), 2, 2, True),
        (days_ago(2, 3), 0, 2, False),  # a whole day without activity breaks it
        (days_ago(0, 0, 1), 2, 2, True),  # duplicates on the same day count once
    ],
)
def test_streak(active: list[date], current: int, longest: int, active_today: bool) -> None:
    streak = compute_streak(active, TODAY)

    assert (streak.current, streak.longest, streak.active_today) == (
        current,
        longest,
        active_today,
    )


def rec_input(
    due: int = 0, enrolled_today: int = 1, recent: list[str] | None = None, modules=ALL_MODULES
) -> RecommendationInput:
    return RecommendationInput(due, enrolled_today, recent or [], frozenset(modules))


def test_due_reviews_come_first() -> None:
    result = recommend(rec_input(due=5, enrolled_today=0))

    assert result is not None
    assert result.target == "review"
    assert "5 powtórek" in result.reason


@pytest.mark.parametrize(
    ("due", "text"), [(1, "1 powtórkę"), (3, "3 powtórki"), (12, "12 powtórek")]
)
def test_review_reason_uses_polish_plural(due: int, text: str) -> None:
    result = recommend(rec_input(due=due))

    assert result is not None and f"Masz {text} na dziś" in result.reason


def test_new_phrases_when_none_were_learned_today() -> None:
    result = recommend(rec_input(enrolled_today=0))

    assert result is not None and result.target == "phrases"


@pytest.mark.parametrize(
    ("recent", "lesson_type"),
    [
        (["vocabulary"], "grammar"),
        (["grammar"], "vocabulary"),
        (["writing", "writing", "writing"], "grammar"),
        (["grammar", "grammar", "grammar"], "vocabulary"),
    ],
)
def test_lessons_alternate_types(recent: list[str], lesson_type: str) -> None:
    result = recommend(rec_input(recent=recent))

    assert result is not None
    assert (result.target, result.lesson_type) == ("lessons", lesson_type)


def test_disabled_modules_are_never_recommended() -> None:
    result = recommend(rec_input(due=3, enrolled_today=0, modules={"conversation"}))

    assert result is not None and result.target == "conversation"
    assert recommend(rec_input(due=3, enrolled_today=0, modules=set())) is None


@pytest.mark.parametrize(
    ("n", "form"),
    [(1, "one"), (2, "few"), (4, "few"), (5, "many"), (12, "many"), (22, "few"), (25, "many")],
)
def test_polish_plural(n: int, form: str) -> None:
    assert plural_pl(n, "one", "few", "many") == form
