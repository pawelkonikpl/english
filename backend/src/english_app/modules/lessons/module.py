from collections.abc import Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.modules import AppModule
from english_app.modules.lessons.models import WORD_ITEM_TYPE
from english_app.modules.lessons.repository import LessonRepository
from english_app.modules.lessons.router import router
from english_app.modules.review.public import CardContent, register_card_loader


async def load_word_cards(session: AsyncSession, ids: Sequence[int]) -> dict[int, CardContent]:
    return {
        word.id: CardContent(
            front=word.word,
            back=word.translation,
            example=word.examples[0] if word.examples else None,
            note=word.mnemonic,
            label="Słówko z lekcji",
        )
        for word in await LessonRepository(session).words_by_ids(ids)
        if word.id is not None
    }


register_card_loader(WORD_ITEM_TYPE, load_word_cards)

module = AppModule(
    key="lessons",
    title="Lekcje",
    router=router,
    depends_on=("profile", "review"),
    nav_order=40,
    icon="graduation-cap",
)
