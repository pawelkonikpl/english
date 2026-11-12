"""Tolerant comparison of a typed answer with the expected text (shared by modules)."""

import re
import unicodedata

_PLACEHOLDER = re.compile(r"\.{3}|…")
_NON_WORD = re.compile(r"[^\w\s']")
_SPACES = re.compile(r"\s+")
_APOSTROPHES = str.maketrans({"\u2019": "'", "\u2018": "'"})  # curly quotes -> '
TYPO_MIN_LENGTH = 5
MAX_TYPOS = 1


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.translate(_APOSTROPHES)
    text = _PLACEHOLDER.sub(" ", text)
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def alternatives(expected: str) -> list[str]:
    """`Sorry. / Excuse me.` accepts either side of the slash."""
    return [part for part in (normalize(p) for p in expected.split(" / ")) if part]


def edit_distance(a: str, b: str) -> int:
    """Optimal string alignment distance: an adjacent swap ("agian") counts as one typo."""
    rows = len(a) + 1
    cols = len(b) + 1
    dist = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        dist[i][0] = i
    for j in range(cols):
        dist[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dist[i][j] = min(dist[i - 1][j] + 1, dist[i][j - 1] + 1, dist[i - 1][j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dist[i][j] = min(dist[i][j], dist[i - 2][j - 2] + 1)
    return dist[-1][-1]


def is_correct(expected: str, given: str, *, allow_typo: bool = True) -> bool:
    """Compare ignoring case, punctuation and spacing.

    `allow_typo` accepts one typo in longer answers. Turn it off when a single letter is the
    point of the exercise (e.g. grammar: "work" vs "works").
    """
    answer = normalize(given)
    if not answer:
        return False
    for option in alternatives(expected):
        if answer == option:
            return True
        if (
            allow_typo
            and len(option) >= TYPO_MIN_LENGTH
            and edit_distance(answer, option) <= MAX_TYPOS
        ):
            return True
    return False
