"""Idempotent loading of the bundled phrase list into the database."""

import json
import logging
from pathlib import Path
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.config import Settings
from english_app.modules.phrases.models import Phrase, PhraseKind, PhraseSource
from english_app.modules.phrases.repository import PhraseRepository

SEED_FILE = Path(__file__).parent / "seed" / "communication_phrases.json"
UPDATABLE_FIELDS = ("tier", "tier_title", "section_title", "position", "polish", "example", "note")

logger = logging.getLogger(__name__)


def load_seed_file(path: Path = SEED_FILE) -> list[dict[str, Any]]:
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return data


async def seed_phrases(session: AsyncSession, settings: Settings) -> None:
    """Insert new seed phrases and refresh texts of existing ones. Commits."""
    repository = PhraseRepository(session)
    inserted = 0
    for entry in load_seed_file():
        existing = await repository.find(entry["section_code"], entry["english"])
        if existing is None:
            repository.add(
                Phrase(
                    **{key: entry[key] for key in ("section_code", "english", *UPDATABLE_FIELDS)},
                    kind=PhraseKind(entry["kind"]),
                    source=PhraseSource.SEED,
                )
            )
            inserted += 1
            continue
        if existing.source is PhraseSource.SEED:
            for key in UPDATABLE_FIELDS:
                setattr(existing, key, entry[key])
            repository.add(existing)
    await session.commit()
    if inserted:
        logger.info("Seeded %d phrases", inserted)
