from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.modules import AppModule
from english_app.modules.phrases.models import ITEM_TYPE
from english_app.modules.phrases.repository import PhraseRepository
from english_app.modules.phrases.router import router
from english_app.modules.phrases.seed import seed_phrases
from english_app.modules.review.public import CardContent, register_card_loader


async def load_phrase_cards(session: AsyncSession, ids: Sequence[int]) -> dict[int, CardContent]:
    return {
        phrase.id: CardContent(
            front=phrase.english,
            back=phrase.polish,
            example=phrase.example,
            note=phrase.note,
            label=phrase.section_title,
        )
        for phrase in await PhraseRepository(session).by_ids(ids)
        if phrase.id is not None
    }


register_card_loader(ITEM_TYPE, load_phrase_cards)

module = AppModule(
    key="phrases",
    title="Frazy",
    router=router,
    depends_on=("profile", "review"),
    on_startup=seed_phrases,
    nav_order=10,
    icon="message-circle",
)
