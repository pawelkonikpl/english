from datetime import date, timedelta

import pytest

from english_app.modules.review.srs import (
    LADDER_DAYS,
    MAX_STEP,
    Grade,
    initial_schedule,
    mastery_for,
    next_schedule,
)

TODAY = date(2026, 11, 12)


def test_three_good_grades_in_a_row_give_a_seven_day_interval() -> None:
    step = initial_schedule(known=False, today=TODAY).step
    intervals = []
    for _ in range(3):
        schedule = next_schedule(step, Grade.GOOD, TODAY)
        step = schedule.step
        intervals.append(schedule.interval_days)

    assert intervals == [1, 3, 7]


def test_again_resets_to_step_zero_and_is_due_today() -> None:
    schedule = next_schedule(4, Grade.AGAIN, TODAY)

    assert (schedule.step, schedule.interval_days, schedule.due_on, schedule.lapsed) == (
        0,
        0,
        TODAY,
        True,
    )


def test_easy_climbs_two_steps() -> None:
    schedule = next_schedule(1, Grade.EASY, TODAY)

    assert schedule.step == 3
    assert schedule.due_on == TODAY + timedelta(days=7)


@pytest.mark.parametrize(("step", "expected_step"), [(0, 1), (1, 1), (3, 3)])
def test_hard_keeps_the_step_but_never_below_one(step: int, expected_step: int) -> None:
    schedule = next_schedule(step, Grade.HARD, TODAY)

    assert schedule.step == expected_step
    assert schedule.interval_days >= 1


def test_steps_are_capped_at_the_end_of_the_ladder() -> None:
    schedule = next_schedule(MAX_STEP, Grade.EASY, TODAY)

    assert schedule.step == MAX_STEP
    assert schedule.interval_days == LADDER_DAYS[-1]


def test_known_phrase_starts_at_step_two_due_in_three_days() -> None:
    schedule = initial_schedule(known=True, today=TODAY)

    assert schedule.step == 2
    assert schedule.due_on == TODAY + timedelta(days=3)


def test_new_phrase_is_due_today() -> None:
    assert initial_schedule(known=False, today=TODAY).due_on == TODAY


@pytest.mark.parametrize(
    ("step", "mastery"), [(0, 0), (1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (7, 3)]
)
def test_mastery_follows_the_interval(step: int, mastery: int) -> None:
    assert mastery_for(step) == mastery
