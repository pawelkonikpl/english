"""Spaced-repetition schedule (pure functions, no I/O).

`step` counts successful levels. A step of n >= 1 means the next review is
`LADDER[n - 1]` days later, so three `good` grades in a row give 1, 3, then 7 days.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

LADDER_DAYS = (1, 3, 7, 14, 30, 60, 120)
MAX_STEP = len(LADDER_DAYS)
KNOWN_START_STEP = 2  # "I know it" skips the first two levels


class Grade(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


@dataclass(frozen=True)
class Schedule:
    step: int
    interval_days: int
    due_on: date
    lapsed: bool


def interval_for(step: int) -> int:
    return 0 if step <= 0 else LADDER_DAYS[min(step, MAX_STEP) - 1]


def next_schedule(step: int, grade: Grade, today: date) -> Schedule:
    if grade is Grade.AGAIN:
        return Schedule(step=0, interval_days=0, due_on=today, lapsed=True)
    if grade is Grade.HARD:
        new_step = max(step, 1)
    elif grade is Grade.GOOD:
        new_step = min(step + 1, MAX_STEP)
    else:
        new_step = min(step + 2, MAX_STEP)
    interval = interval_for(new_step)
    return Schedule(
        step=new_step, interval_days=interval, due_on=today + timedelta(days=interval), lapsed=False
    )


def initial_schedule(*, known: bool, today: date) -> Schedule:
    step = KNOWN_START_STEP if known else 0
    interval = interval_for(step)
    return Schedule(
        step=step, interval_days=interval, due_on=today + timedelta(days=interval), lapsed=False
    )


def mastery_for(step: int) -> int:
    """0 = new, 1 = learning (< 7 days), 2 = familiar (7-29 days), 3 = mastered (>= 30 days)."""
    interval = interval_for(step)
    if step == 0:
        return 0
    if interval < 7:
        return 1
    if interval < 30:
        return 2
    return 3
