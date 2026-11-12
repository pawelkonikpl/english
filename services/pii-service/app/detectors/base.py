"""Contract shared by every PII detector backend."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class PiiCategory(StrEnum):
    """Model-independent PII categories exposed by the API.

    Each backend maps its own labels onto these, so clients keep the same contract
    when the model changes. Labels without a counterpart become ``OTHER``.
    """

    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"
    LOCATION = "LOCATION"
    URL = "URL"
    DATE = "DATE"
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
    ID_NUMBER = "ID_NUMBER"
    SECRET = "SECRET"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class PiiEntity:
    """A PII span found in a text.

    Attributes:
        category: Model-independent category of the span.
        source_label: Label as the backend reported it, e.g. ``PERSON_NAME``.
        start: Offset of the first character in the analysed text.
        end: Offset one past the last character, so ``text[start:end]`` is the span.
        score: Detector confidence between 0 and 1.
    """

    category: PiiCategory
    source_label: str
    start: int
    end: int
    score: float


class PiiDetector(Protocol):
    """Finds PII spans in a text."""

    def detect(self, text: str) -> list[PiiEntity]:
        """Return the PII spans found in ``text``, ordered by start offset."""
        ...
