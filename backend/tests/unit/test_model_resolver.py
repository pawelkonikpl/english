from typing import Any

import pytest

from english_app.core.config import ProviderModelDefaults
from english_app.llm.base import ModelTier
from english_app.llm.models import ModelResolver


class InMemorySettings:
    """Stands in for AppSettingRepository."""

    def __init__(self) -> None:
        self.values: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self.values.get(key)

    async def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)


def resolver(main: str | None, fast: str | None, store: InMemorySettings, provider: str = "p"):
    return ModelResolver(provider, ProviderModelDefaults(main, fast, []), store)  # type: ignore[arg-type]


async def test_env_values_are_used_by_default() -> None:
    models = resolver("big", "small", InMemorySettings())

    assert await models.resolve(ModelTier.MAIN) == "big"
    assert await models.resolve(ModelTier.FAST) == "small"


async def test_override_from_settings_wins_over_env() -> None:
    store = InMemorySettings()
    models = resolver("big", "small", store)
    await models.set_override(ModelTier.FAST, "custom")

    assert await models.resolve(ModelTier.FAST) == "custom"
    assert await models.resolve(ModelTier.MAIN) == "big"


async def test_fast_falls_back_to_the_main_model() -> None:
    store = InMemorySettings()
    models = resolver("big", None, store)
    assert await models.resolve(ModelTier.FAST) == "big"

    await models.set_override(ModelTier.MAIN, "bigger")
    assert await models.resolve(ModelTier.FAST) == "bigger"


async def test_nothing_configured_means_provider_default() -> None:
    models = resolver(None, None, InMemorySettings())

    assert await models.resolve(ModelTier.MAIN) is None
    assert await models.resolve(ModelTier.FAST) is None


async def test_removing_an_override_restores_env() -> None:
    store = InMemorySettings()
    models = resolver("big", "small", store)
    await models.set_override(ModelTier.MAIN, "custom")
    await models.set_override(ModelTier.MAIN, None)

    assert await models.resolve(ModelTier.MAIN) == "big"


async def test_overrides_are_kept_per_provider() -> None:
    store = InMemorySettings()
    await resolver("claude", None, store, provider="claude_code").set_override(
        ModelTier.MAIN, "claude-custom"
    )

    copilot = resolver(None, None, store, provider="copilot")

    assert await copilot.resolve(ModelTier.MAIN) is None


async def test_describe_reports_env_override_and_effective() -> None:
    store = InMemorySettings()
    models = resolver("big", None, store)
    await models.set_override(ModelTier.FAST, "quick")

    described = {d.tier: d for d in await models.describe()}

    assert (described[ModelTier.MAIN].env_model, described[ModelTier.MAIN].effective) == (
        "big",
        "big",
    )
    assert (described[ModelTier.FAST].override, described[ModelTier.FAST].effective) == (
        "quick",
        "quick",
    )


@pytest.mark.parametrize("value", ["", 123, None])
async def test_invalid_stored_values_are_ignored(value: Any) -> None:
    store = InMemorySettings()
    store.values["llm.p.main"] = value

    assert await resolver("big", None, store).resolve(ModelTier.MAIN) == "big"
