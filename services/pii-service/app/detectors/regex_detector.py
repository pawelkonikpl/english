"""Deterministic PII detector built from regular expressions.

It needs no model download, which makes it the backend for local development and
tests, but it only finds well-formatted identifiers: e-mail addresses, URLs, phone
numbers and IBANs. Names and addresses need a model-backed backend.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.detectors.base import PiiCategory, PiiEntity

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}(?![\w-])")
_URL = re.compile(r"(?<![\w@])(?:https?://|www\.)[^\s<>\"'()\[\]{}]+", re.IGNORECASE)
_IBAN = re.compile(
    r"(?<![A-Z0-9])[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?(?![A-Z0-9])"
)
_PHONE = re.compile(r"(?<![\w+(])(?:\+|\()?\d[\d ().-]{7,}\d(?!\w)")

_URL_TRAILING_PUNCTUATION = ".,;:!?"
# E.164 allows at most 15 digits; 9 is the shortest national number we accept,
# which also keeps ISO dates such as 2025-01-09 (8 digits) out.
_PHONE_MIN_DIGITS = 9
_PHONE_MAX_DIGITS = 15
_IBAN_MIN_LENGTH = 15
_IBAN_MAX_LENGTH = 34
_IBAN_CHECKSUM_REMAINDER = 1
_IBAN_MODULUS = 97
_REGEX_SCORE = 1.0


@dataclass(frozen=True, slots=True)
class _Rule:
    category: PiiCategory
    pattern: re.Pattern[str]
    clean: Callable[[str], str | None]


def _unchanged(value: str) -> str | None:
    return value


def _clean_url(value: str) -> str | None:
    return value.rstrip(_URL_TRAILING_PUNCTUATION) or None


def _clean_phone(value: str) -> str | None:
    digits = sum(character.isdigit() for character in value)
    return value if _PHONE_MIN_DIGITS <= digits <= _PHONE_MAX_DIGITS else None


def _clean_iban(value: str) -> str | None:
    return value if _is_valid_iban(value.replace(" ", "")) else None


def _is_valid_iban(iban: str) -> bool:
    """Check the ISO 13616 mod-97 checksum."""
    if not _IBAN_MIN_LENGTH <= len(iban) <= _IBAN_MAX_LENGTH:
        return False
    rearranged = iban[4:] + iban[:4]
    as_digits = "".join(str(int(character, 36)) for character in rearranged)
    return int(as_digits) % _IBAN_MODULUS == _IBAN_CHECKSUM_REMAINDER


# When matches overlap, the longest one wins; this order only breaks ties.
_RULES = (
    _Rule(PiiCategory.EMAIL, _EMAIL, _unchanged),
    _Rule(PiiCategory.URL, _URL, _clean_url),
    _Rule(PiiCategory.ACCOUNT_NUMBER, _IBAN, _clean_iban),
    _Rule(PiiCategory.PHONE, _PHONE, _clean_phone),
)


class RegexPiiDetector:
    """Finds well-formatted identifiers with regular expressions."""

    def detect(self, text: str) -> list[PiiEntity]:
        candidates: list[tuple[int, PiiEntity]] = []
        for priority, rule in enumerate(_RULES):
            for match in rule.pattern.finditer(text):
                value = rule.clean(match.group())
                if value is None:
                    continue
                entity = PiiEntity(
                    category=rule.category,
                    source_label=rule.category.value,
                    start=match.start(),
                    end=match.start() + len(value),
                    score=_REGEX_SCORE,
                )
                candidates.append((priority, entity))

        candidates.sort(key=lambda item: (-(item[1].end - item[1].start), item[0]))
        accepted: list[PiiEntity] = []
        for _, entity in candidates:
            if not any(_overlaps(entity, kept) for kept in accepted):
                accepted.append(entity)
        return sorted(accepted, key=lambda entity: entity.start)


def _overlaps(first: PiiEntity, second: PiiEntity) -> bool:
    return first.start < second.end and second.start < first.end
