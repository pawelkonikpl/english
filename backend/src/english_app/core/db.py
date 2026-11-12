"""Database engine, session dependency and startup migrations."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated

from alembic import command
from alembic.config import Config
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.config import Settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"

SessionFactory = async_sessionmaker[AsyncSession]


def create_engine(settings: Settings) -> AsyncEngine:
    sqlite_path = settings.sqlite_path
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(settings.database_url)


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    # expire_on_commit=False: reading attributes after commit must not lazy-load under asyncio.
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _upgrade_to_head(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


async def run_migrations(database_url: str) -> None:
    # Alembic's env.py drives its own event loop, so it runs in a worker thread.
    await asyncio.to_thread(_upgrade_to_head, database_url)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: SessionFactory = request.app.state.session_factory
    # Closing the session rolls back whatever a service did not commit.
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
