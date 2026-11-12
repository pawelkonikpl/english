"""Pure progress rules: XP per activity, streaks, achievements and the daily recommendation."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from english_app.core.events import ActivityKind, LearningActivity

REVIEW_POINTS = {"good": 1.0, "easy": 1.0, "hard": 0.5, "again": 0.0}
PHRASE_ENROLLED_POINTS = 1.0
CORRECT_ANSWER_POINTS = 2.0
MAX_CONVERSATION_POINTS = 10.0


def points_for(activity: LearningActivity) -> float:
    details = activity.details
    match activity.kind:
        case ActivityKind.REVIEW_GRADED:
            return REVIEW_POINTS.get(str(details.get("grade")), 0.0)
        case ActivityKind.PHRASE_ENROLLED:
            return PHRASE_ENROLLED_POINTS
        case ActivityKind.LESSON_ANSWERED:
            return CORRECT_ANSWER_POINTS if details.get("correct") else 0.0
        case ActivityKind.CONVERSATION_FINISHED:
            score = float(details.get("score", 0))
            return max(0.0, min(score, MAX_CONVERSATION_POINTS))
        case _:
            return 0.0


@dataclass(frozen=True)
class Streak:
    current: int
    longest: int
    active_today: bool


def compute_streak(active_days: Iterable[date], today: date) -> Streak:
    """A streak counts consecutive active days ending today, or yesterday if today is empty."""
    days = sorted(set(active_days))
    day_set = set(days)

    longest = run = 0
    previous: date | None = None
    for day in days:
        run = run + 1 if previous is not None and day - previous == timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day

    active_today = today in day_set
    cursor = today if active_today else today - timedelta(days=1)
    current = 0
    while cursor in day_set:
        current += 1
        cursor -= timedelta(days=1)
    return Streak(current=current, longest=longest, active_today=active_today)


@dataclass(frozen=True)
class ProgressStats:
    phrases_enrolled: int
    reviews_done: int
    lessons_completed: int
    conversations_finished: int
    current_streak: int
    longest_streak: int
    milestones: frozenset[str]


@dataclass(frozen=True)
class Achievement:
    key: str
    title: str
    description: str
    icon: str
    is_unlocked: Callable[[ProgressStats], bool]


def _phrases(n: int) -> Callable[[ProgressStats], bool]:
    return lambda s: s.phrases_enrolled >= n


def _streak(n: int) -> Callable[[ProgressStats], bool]:
    return lambda s: s.longest_streak >= n


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement(
        "phrases_10", "Pierwsze 10 fraz", "Zacznij naukę 10 fraz.", "sparkles", _phrases(10)
    ),
    Achievement("phrases_50", "50 fraz", "Zacznij naukę 50 fraz.", "book-open", _phrases(50)),
    Achievement("phrases_100", "100 fraz", "Zacznij naukę 100 fraz.", "library", _phrases(100)),
    Achievement("phrases_200", "200 fraz", "Zacznij naukę 200 fraz.", "crown", _phrases(200)),
    Achievement(
        "phrases_tier_1",
        "Ratownik",
        "Zacznij naukę wszystkich fraz ratunkowych z Poziomu 1.",
        "life-buoy",
        lambda s: "phrases_tier_1" in s.milestones,
    ),
    Achievement("streak_3", "3 dni z rzędu", "Ucz się 3 dni z rzędu.", "flame", _streak(3)),
    Achievement("streak_7", "Tydzień z rzędu", "Ucz się 7 dni z rzędu.", "flame", _streak(7)),
    Achievement("streak_30", "Miesiąc z rzędu", "Ucz się 30 dni z rzędu.", "trophy", _streak(30)),
    Achievement(
        "reviews_100",
        "100 powtórek",
        "Zrób 100 powtórek.",
        "repeat",
        lambda s: s.reviews_done >= 100,
    ),
    Achievement(
        "first_lesson",
        "Pierwsza lekcja",
        "Ukończ pierwszą lekcję z AI.",
        "graduation-cap",
        lambda s: s.lessons_completed >= 1,
    ),
    Achievement(
        "first_conversation",
        "Pierwsza rozmowa",
        "Ukończ pierwszą rozmowę z AI.",
        "messages-square",
        lambda s: s.conversations_finished >= 1,
    ),
)


@dataclass(frozen=True)
class Recommendation:
    target: str  # route key the UI opens: "review", "phrases", "lessons", "conversation"
    lesson_type: str | None
    title: str
    reason: str


@dataclass(frozen=True)
class RecommendationInput:
    due_reviews: int
    phrases_enrolled_today: int
    recent_lesson_types: list[str]  # newest first
    enabled_modules: frozenset[str]


VOCABULARY = "vocabulary"
GRAMMAR = "grammar"
SAME_TYPE_LIMIT = 3


def recommend(data: RecommendationInput) -> Recommendation | None:
    """Rules from the original system prompt, limited to enabled modules."""
    enabled = data.enabled_modules
    if data.due_reviews > 0 and "review" in enabled:
        return Recommendation(
            "review",
            None,
            "Powtórki",
            f"Masz {data.due_reviews} powtórek na dziś. Zacznij od nich!",
        )
    if data.phrases_enrolled_today == 0 and "phrases" in enabled:
        return Recommendation(
            "phrases", None, "Nowe frazy", "Dziś nie było jeszcze nowych fraz. Poznaj kilka!"
        )
    if "lessons" in enabled:
        recent = data.recent_lesson_types
        last = recent[0] if recent else None
        repeated = len(recent) >= SAME_TYPE_LIMIT and len(set(recent[:SAME_TYPE_LIMIT])) == 1
        if last == VOCABULARY or (repeated and last != GRAMMAR):
            return Recommendation(
                "lessons", GRAMMAR, "Lekcja gramatyki", "Po słówkach czas na gramatykę."
            )
        if last == GRAMMAR or repeated:
            return Recommendation(
                "lessons", VOCABULARY, "Lekcja słówek", "Po gramatyce czas na nowe słówka."
            )
    if "conversation" in enabled:
        return Recommendation(
            "conversation", None, "Rozmowa z AI", "Przećwicz poznane frazy w rozmowie."
        )
    if "lessons" in enabled:
        return Recommendation("lessons", VOCABULARY, "Lekcja słówek", "Poznaj 5 nowych słów.")
    return None
