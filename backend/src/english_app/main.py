"""Application factory: wires settings, database, LLM provider and enabled modules."""

import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI

from english_app.core import router as core_router
from english_app.core.clock import SystemClock
from english_app.core.config import Settings, get_settings
from english_app.core.db import create_engine, create_session_factory, run_migrations
from english_app.core.errors import register_error_handlers
from english_app.core.events import EventBus
from english_app.core.modules import AppModule, ModuleContext, resolve_enabled_modules
from english_app.llm import router as llm_router
from english_app.llm.base import LLMProvider
from english_app.llm.factory import create_llm_provider
from english_app.modules import AVAILABLE_MODULES

logger = logging.getLogger(__name__)

API_PREFIX = "/api"


def create_app(
    settings: Settings | None = None,
    *,
    available_modules: Sequence[AppModule] | None = None,
    llm_provider: LLMProvider | None = None,
) -> FastAPI:
    """Build the FastAPI app. Arguments exist so tests can swap configuration and fakes."""
    settings = settings or get_settings()
    modules = resolve_enabled_modules(
        AVAILABLE_MODULES if available_modules is None else available_modules,
        settings.enabled_modules,
    )
    provider = llm_provider or create_llm_provider(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await run_migrations(settings.database_url)
        engine = create_engine(settings)
        app.state.session_factory = create_session_factory(engine)
        async with app.state.session_factory() as session:
            for module in modules:
                if module.on_startup is not None:
                    await module.on_startup(session, settings)
        logger.info(
            "Started with LLM provider '%s' and modules: %s",
            provider.name,
            ", ".join(m.key for m in modules) or "(none)",
        )
        try:
            yield
        finally:
            await provider.aclose()
            await engine.dispose()

    app = FastAPI(title="English Learning App", lifespan=lifespan)
    app.state.settings = settings
    app.state.llm_provider = provider
    app.state.modules = modules
    app.state.clock = SystemClock(settings.app_timezone)
    app.state.event_bus = EventBus()

    context = ModuleContext(settings=settings, clock=app.state.clock)
    for module in modules:
        module.register_events(app.state.event_bus, context)
        app.include_router(module.router, prefix=f"{API_PREFIX}/{module.key}")

    app.include_router(core_router.router, prefix=API_PREFIX)
    app.include_router(llm_router.router, prefix=API_PREFIX)
    register_error_handlers(app)
    return app
