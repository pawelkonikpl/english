"""Business rules for detecting and redacting PII. Framework-free."""

from collections.abc import Collection
from dataclasses import dataclass

from app.detectors.base import PiiCategory, PiiDetector, PiiEntity


@dataclass(frozen=True, slots=True)
class RedactionResult:
    """Text with PII replaced by ``[CATEGORY]`` placeholders.

    Entity offsets refer to the original text, not to ``redacted_text``.
    """

    redacted_text: str
    entities: list[PiiEntity]


class PiiService:
    """Filters detector output and redacts PII.

    The analysed text is never logged: it is the data this service protects.
    """

    def __init__(self, detector: PiiDetector, *, backend: str, default_min_score: float) -> None:
        self._detector = detector
        self._backend = backend
        self._default_min_score = default_min_score

    @property
    def backend(self) -> str:
        return self._backend

    def detect(
        self,
        text: str,
        *,
        categories: Collection[PiiCategory] | None = None,
        min_score: float | None = None,
    ) -> list[PiiEntity]:
        """Return entities of the requested categories that reach the score threshold."""
        threshold = self._default_min_score if min_score is None else min_score
        return [
            entity
            for entity in self._detector.detect(text)
            if entity.score >= threshold and (categories is None or entity.category in categories)
        ]

    def redact(
        self,
        text: str,
        *,
        categories: Collection[PiiCategory] | None = None,
        min_score: float | None = None,
    ) -> RedactionResult:
        """Replace every detected entity with a ``[CATEGORY]`` placeholder."""
        entities = self.detect(text, categories=categories, min_score=min_score)
        return RedactionResult(redacted_text=_replace_entities(text, entities), entities=entities)


def _replace_entities(text: str, entities: list[PiiEntity]) -> str:
    parts: list[str] = []
    cursor = 0
    for start, end, category in _merge_overlapping(entities):
        parts.append(text[cursor:start])
        parts.append(f"[{category}]")
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def _merge_overlapping(entities: list[PiiEntity]) -> list[tuple[int, int, PiiCategory]]:
    """Join overlapping entities so that no part of either one survives redaction.

    The merged region takes the category of the entity that starts first.
    """
    merged: list[tuple[int, int, PiiCategory]] = []
    for entity in sorted(entities, key=lambda item: (item.start, -item.end)):
        if merged and entity.start < merged[-1][1]:
            start, end, category = merged[-1]
            merged[-1] = (start, max(end, entity.end), category)
        else:
            merged.append((entity.start, entity.end, entity.category))
    return merged
