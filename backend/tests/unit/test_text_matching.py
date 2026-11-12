import pytest

from english_app.core.text_matching import edit_distance, is_correct, normalize


@pytest.mark.parametrize(
    ("expected", "given"),
    [
        ("Sorry, could you say that again?", "sorry could you say that again"),
        ("Sorry, could you say that again?", "Sorry, could you say that agian?"),  # swapped letters
        ("I don't think so.", "I don\u2019t think so"),  # curly apostrophe
        ("Well... / Hmm...", "hmm"),  # either alternative
        ("Give me a second. / Just a sec.", "just a sec"),
        ("It depends on...", "it depends on"),  # placeholder dots ignored
        ("I agree.", "i agre"),  # one typo in a 7-letter answer
    ],
)
def test_accepts_reasonable_answers(expected: str, given: str) -> None:
    assert is_correct(expected, given)


@pytest.mark.parametrize(
    ("expected", "given"),
    [
        ("take", "tak"),  # short answers must be exact
        ("Sorry, could you say that again?", "could you speak more slowly"),
        ("I agree.", ""),
        ("I agree.", "   "),
        ("I agree.", "i agr"),  # two edits
    ],
)
def test_rejects_wrong_answers(expected: str, given: str) -> None:
    assert not is_correct(expected, given)


def test_normalize_strips_punctuation_case_and_extra_spaces() -> None:
    assert normalize("  Hello,   WORLD!!  ") == "hello world"


def test_edit_distance_counts_adjacent_swap_as_one() -> None:
    assert edit_distance("again", "agian") == 1
    assert edit_distance("kitten", "sitting") == 3


def test_typos_can_be_disallowed_for_grammar_exercises() -> None:
    assert is_correct("works", "work")
    assert not is_correct("works", "work", allow_typo=False)
    assert is_correct("works", "Works!", allow_typo=False)
