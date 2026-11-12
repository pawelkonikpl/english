"""Feature modules and the logic that decides which of them are loaded."""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from fastapi import APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.clock import Clock
from english_app.core.config import Settings
from english_app.core.errors import ConfigurationError
from english_app.core.events import EventBus


@dataclass(frozen=True)
class ModuleContext:
    """Application-wide objects a module may need when it registers event handlers."""

    settings: Settings
    clock: Clock


StartupHook = Callable[[AsyncSession, Settings], Awaitable[None]]
EventRegistration = Callable[[EventBus, ModuleContext], None]


def _no_events(bus: EventBus, context: ModuleContext) -> None:
    return None


@dataclass(frozen=True)
class AppModule:
    """A self-contained feature: its API router, startup work and event subscriptions.

    Modules never import each other's internals. They talk through events and the
    small public services documented in each module's `__init__.py`.
    """

    key: str
    title: str
    router: APIRouter
    depends_on: tuple[str, ...] = ()
    register_events: EventRegistration = _no_events
    on_startup: StartupHook | None = None
    nav_order: int = 100
    icon: str = "circle"


def resolve_enabled_modules(
    available: Sequence[AppModule], enabled_keys: Sequence[str]
) -> list[AppModule]:
    """Return enabled modules ordered so that dependencies come first.

    An empty `enabled_keys` enables every available module.

    Raises:
        ConfigurationError: unknown module key or a missing dependency.
    """
    by_key = {module.key: module for module in available}
    keys = list(enabled_keys) or list(by_key)

    unknown = [key for key in keys if key not in by_key]
    if unknown:
        raise ConfigurationError(
            f"Unknown modules in ENABLED_MODULES: {', '.join(unknown)}. "
            f"Available: {', '.join(by_key)}"
        )

    enabled = set(keys)
    for key in keys:
        missing = [dep for dep in by_key[key].depends_on if dep not in enabled]
        if missing:
            raise ConfigurationError(
                f"Module '{key}' requires {', '.join(missing)}; add it to ENABLED_MODULES"
            )

    ordered: list[AppModule] = []
    visited: set[str] = set()

    def visit(key: str) -> None:
        if key in visited:
            return
        visited.add(key)
        for dep in by_key[key].depends_on:
            visit(dep)
        ordered.append(by_key[key])

    for key in keys:
        visit(key)
    return ordered
