from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from english_app.core.config import Settings
from english_app.main import create_app
from tests.support import FrozenClock, RecordingProvider

# Noon in Warsaw on a Thursday: far from midnight and DST changes unless a test moves it.
DEFAULT_NOW = datetime(2026, 11, 12, 11, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock(DEFAULT_NOW)


@pytest.fixture
def provider() -> RecordingProvider:
    return RecordingProvider()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]  # never read the developer's .env in tests
        llm_provider="fake",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        enabled_modules=[],
        daily_new_phrases=10,
    )


@pytest.fixture
async def app(
    settings: Settings, provider: RecordingProvider, clock: FrozenClock
) -> AsyncIterator[FastAPI]:
    application = create_app(settings, llm_provider=provider, clock=clock)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
