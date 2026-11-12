"""Registry of card content loaders, one per item type.

Review stores only scheduling state. Modules that own content (phrases, lesson words)
register a loader here, so review never imports their internals.
"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from sqlmodel.ext.asyncio.session import AsyncSession


@dataclass(frozen=True)
class CardContent:
    front: str  # English side
    back: str  # translation / meaning
    example: str | None = None
    note: str | None = None
    label: str | None = None  # e.g. section title shown on the card


CardLoader = Callable[[AsyncSession, Sequence[int]], Awaitable[dict[int, CardContent]]]

_LOADERS: dict[str, CardLoader] = {}


def register_card_loader(item_type: str, loader: CardLoader) -> None:
    _LOADERS[item_type] = loader


async def load_cards(
    session: AsyncSession, refs: Sequence[tuple[str, int]]
) -> dict[tuple[str, int], CardContent]:
    by_type: dict[str, list[int]] = {}
    for item_type, item_id in refs:
        by_type.setdefault(item_type, []).append(item_id)
    cards: dict[tuple[str, int], CardContent] = {}
    for item_type, ids in by_type.items():
        loader = _LOADERS.get(item_type)
        if loader is None:
            continue  # the owning module is disabled; its items are skipped
        for item_id, content in (await loader(session, ids)).items():
            cards[(item_type, item_id)] = content
    return cards
