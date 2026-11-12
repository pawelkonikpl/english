"""In-process event bus that lets modules react to each other without imports.

Handlers run inside the publisher's database session, so their writes are committed
together with the change that caused the event.
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sqlmodel.ext.asyncio.session import AsyncSession

EventT = TypeVar("EventT")
Handler = Callable[[Any, AsyncSession], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Any], list[Handler]] = defaultdict(list)

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT, AsyncSession], Awaitable[None]]
    ) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: object, session: AsyncSession) -> None:
        for handler in self._handlers.get(type(event), []):
            await handler(event, session)
