"""Turns per-token model predictions into character spans.

Pure functions without model dependencies, shared by every token-classification
backend. Both tagging schemes in use are supported: BIO (bardsai models) and
BIOES (openai/privacy-filter).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field, replace

OUTSIDE_LABEL = "O"
_SPAN_PREFIXES = frozenset({"B", "I", "E", "S"})
_OPENING_PREFIXES = frozenset({"B", "S"})
_CLOSING_PREFIXES = frozenset({"E", "S"})


@dataclass(frozen=True, slots=True)
class TokenPrediction:
    """Model output for one token: character offsets, tag (e.g. ``B-PERSON``) and probability."""

    start: int
    end: int
    tag: str
    score: float


@dataclass(frozen=True, slots=True)
class LabeledSpan:
    """A character span with a model label stripped of its boundary prefix."""

    start: int
    end: int
    label: str
    score: float


@dataclass(slots=True)
class _OpenSpan:
    label: str
    start: int
    end: int
    scores: list[float] = field(default_factory=list)

    def close(self) -> LabeledSpan:
        return LabeledSpan(
            start=self.start,
            end=self.end,
            label=self.label,
            score=sum(self.scores) / len(self.scores),
        )


def split_tag(tag: str) -> tuple[str, str]:
    """Split ``B-PERSON`` into ``("B", "PERSON")``.

    A tag without a recognised prefix is treated as the inside of a span.
    """
    prefix, separator, label = tag.partition("-")
    if separator and prefix in _SPAN_PREFIXES:
        return prefix, label
    return "I", tag


def decode_spans(tokens: Sequence[TokenPrediction]) -> list[LabeledSpan]:
    """Group token predictions, ordered by offset, into labelled spans.

    Decoding is lenient: a span may start with an inside tag and may lack an end
    tag, because argmax predictions do not always follow the tagging scheme.
    A new span starts on a B-/S- tag or when the label changes; E-/S- tags and
    the outside tag close the current span.
    """
    spans: list[LabeledSpan] = []
    current: _OpenSpan | None = None
    for token in tokens:
        if token.tag == OUTSIDE_LABEL:
            if current is not None:
                spans.append(current.close())
                current = None
            continue

        prefix, label = split_tag(token.tag)
        if current is None or prefix in _OPENING_PREFIXES or label != current.label:
            if current is not None:
                spans.append(current.close())
            current = _OpenSpan(label=label, start=token.start, end=token.end)
        current.end = token.end
        current.scores.append(token.score)

        if prefix in _CLOSING_PREFIXES:
            spans.append(current.close())
            current = None

    if current is not None:
        spans.append(current.close())
    return spans


def refine_spans(text: str, spans: Sequence[LabeledSpan]) -> list[LabeledSpan]:
    """Align spans with the text so that redaction does not leak fragments.

    Surrounding whitespace is trimmed (byte-level BPE offsets include the leading
    space), spans are widened to whole words (a tagged sub-word ``Kowal`` covers
    ``Kowalski``), and overlapping spans with the same label are merged.
    """
    aligned = [
        aligned_span for span in spans if (aligned_span := _align_to_words(text, span)) is not None
    ]
    aligned.sort(key=lambda span: (span.start, -span.end))

    merged: list[LabeledSpan] = []
    for span in aligned:
        previous = merged[-1] if merged else None
        if previous is not None and previous.label == span.label and span.start < previous.end:
            merged[-1] = replace(
                previous,
                end=max(previous.end, span.end),
                score=max(previous.score, span.score),
            )
        else:
            merged.append(span)
    return merged


def _align_to_words(text: str, span: LabeledSpan) -> LabeledSpan | None:
    start, end = span.start, span.end
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    if start == end:
        return None

    while start > 0 and text[start - 1].isalnum():
        start -= 1
    while end < len(text) and text[end].isalnum():
        end += 1
    return replace(span, start=start, end=end)
