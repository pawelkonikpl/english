"""Test doubles shared by unit and integration tests."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from english_app.llm.base import ChatMessage, LLMError, LLMResult, SchemaT
from english_app.llm.providers.fake import FakeProvider

WARSAW = "Europe/Warsaw"


class FrozenClock:
    """A clock the test moves by hand. `now` is UTC; dates use the learner's zone."""

    def __init__(self, now: datetime, timezone: str = WARSAW) -> None:
        self._now = now
        self._zone = ZoneInfo(timezone)

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self.local_date(self._now)

    def local_date(self, moment: datetime) -> date:
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return moment.astimezone(self._zone).date()

    def day_bounds(self, day: date) -> tuple[datetime, datetime]:
        start = datetime.combine(day, time.min, tzinfo=self._zone)
        end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=self._zone)
        return start.astimezone(UTC), end.astimezone(UTC)

    def set(self, now: datetime) -> None:
        self._now = now

    def advance(self, **delta: float) -> None:
        self._now += timedelta(**delta)


class RecordingProvider(FakeProvider):
    """Fake provider that records which model each call asked for and can be made to fail."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str | None]] = []  # (schema name or "text", model)
        self.prompts: list[
            tuple[str, str, list[ChatMessage]]
        ] = []  # (schema name, system, messages)
        self.fail_with: LLMError | None = None

    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> LLMResult[str]:
        self.calls.append(("text", model))
        self.prompts.append(("text", system, list(messages)))
        if self.fail_with:
            raise self.fail_with
        return await super().complete(system=system, messages=messages, model=model)

    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        model: str | None,
    ) -> LLMResult[SchemaT]:
        self.calls.append((schema.__name__, model))
        self.prompts.append((schema.__name__, system, list(messages)))
        if self.fail_with:
            raise self.fail_with
        return await super().complete_structured(
            system=system, messages=messages, schema=schema, model=model
        )

    def calls_for(self, name: str) -> list[str | None]:
        return [model for called, model in self.calls if called == name]

    def systems_for(self, name: str) -> list[str]:
        return [system for called, system, _ in self.prompts if called == name]


@asynccontextmanager
async def serve(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Run the app's startup/shutdown around an HTTP client, like a real server would."""
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        yield client
