from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.modules.conversation.models import Conversation, ConversationMessage


class ConversationRepository:
    """Queries for conversations and their messages. Never commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, conversation_id: int) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def messages(self, conversation_id: int) -> list[ConversationMessage]:
        statement = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(col(ConversationMessage.id))
        )
        return list((await self._session.exec(statement)).all())

    async def recent(self, limit: int) -> list[tuple[Conversation, int]]:
        counts = (
            select(ConversationMessage.conversation_id, func.count().label("n"))
            .group_by(col(ConversationMessage.conversation_id))
            .subquery()
        )
        statement = (
            select(Conversation, func.coalesce(counts.c.n, 0))
            .outerjoin(counts, col(Conversation.id) == counts.c.conversation_id)
            .order_by(col(Conversation.started_at).desc())
            .limit(limit)
        )
        return [(c, int(n)) for c, n in (await self._session.exec(statement)).all()]

    def add(self, entity: Conversation | ConversationMessage) -> None:
        self._session.add(entity)
