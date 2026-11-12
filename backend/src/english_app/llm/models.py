"""Decides which model each task tier uses.

Order (first non-empty wins):
1. override saved from the settings screen (`app_setting` key `llm.<provider>.<tier>`),
2. `.env` value for the active provider,
3. for the fast tier only: the main tier's model,
4. `None`, meaning "the provider's default model".
"""

from dataclasses import dataclass

from english_app.core.app_settings import AppSettingRepository
from english_app.core.config import ProviderModelDefaults
from english_app.llm.base import ModelTier


@dataclass(frozen=True)
class TierModelSettings:
    tier: ModelTier
    env_model: str | None
    override: str | None
    effective: str | None


def override_key(provider: str, tier: ModelTier) -> str:
    return f"llm.{provider}.{tier.value}"


class ModelResolver:
    def __init__(
        self, provider: str, defaults: ProviderModelDefaults, settings: AppSettingRepository
    ) -> None:
        self._provider = provider
        self._defaults = defaults
        self._settings = settings

    async def resolve(self, tier: ModelTier) -> str | None:
        main = await self._override(ModelTier.MAIN) or self._defaults.main
        if tier is ModelTier.MAIN:
            return main
        return await self._override(ModelTier.FAST) or self._defaults.fast or main

    async def describe(self) -> list[TierModelSettings]:
        return [
            TierModelSettings(
                tier=tier,
                env_model=self._env_model(tier),
                override=await self._override(tier),
                effective=await self.resolve(tier),
            )
            for tier in ModelTier
        ]

    async def set_override(self, tier: ModelTier, model: str | None) -> None:
        """Save an override, or remove it when `model` is None. Does not commit."""
        key = override_key(self._provider, tier)
        if model is None:
            await self._settings.delete(key)
        else:
            await self._settings.set(key, model)

    async def _override(self, tier: ModelTier) -> str | None:
        value = await self._settings.get(override_key(self._provider, tier))
        return value if isinstance(value, str) and value else None

    def _env_model(self, tier: ModelTier) -> str | None:
        return self._defaults.main if tier is ModelTier.MAIN else self._defaults.fast
