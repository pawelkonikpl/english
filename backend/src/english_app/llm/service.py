"""The only entry point modules use to talk to a language model."""

import time
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from english_app.core.app_settings import AppSettingRepository
from english_app.core.config import Settings
from english_app.core.db import SessionDep
from english_app.core.dependencies import SettingsDep
from english_app.core.errors import InvalidInputError
from english_app.llm.base import (
    ChatMessage,
    LLMError,
    LLMProvider,
    LLMResult,
    ModelInfo,
    ModelTier,
    SchemaT,
)
from english_app.llm.models import ModelResolver, TierModelSettings

TEST_SYSTEM_PROMPT = "You are a connectivity check. Reply with the single word: OK"


@dataclass(frozen=True)
class ProviderStatus:
    provider: str
    models: dict[ModelTier, str | None]
    available: bool
    detail: str | None


@dataclass(frozen=True)
class ModelTestResult:
    ok: bool
    model: str | None
    latency_ms: int
    detail: str | None


class LLMService:
    """Resolves the model for a task tier and delegates to the active provider."""

    def __init__(
        self, provider: LLMProvider, resolver: ModelResolver, session: AsyncSession
    ) -> None:
        self._provider = provider
        self._resolver = resolver
        self._session = session

    @property
    def provider_name(self) -> str:
        return self._provider.name

    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], tier: ModelTier
    ) -> LLMResult[str]:
        model = await self._resolver.resolve(tier)
        return await self._provider.complete(system=system, messages=messages, model=model)

    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        tier: ModelTier,
    ) -> LLMResult[SchemaT]:
        model = await self._resolver.resolve(tier)
        return await self._provider.complete_structured(
            system=system, messages=messages, schema=schema, model=model
        )

    async def stream(
        self, *, system: str, messages: Sequence[ChatMessage], tier: ModelTier
    ) -> AsyncIterator[str]:
        model = await self._resolver.resolve(tier)
        async for chunk in self._provider.stream(system=system, messages=messages, model=model):
            yield chunk

    async def list_models(self) -> list[ModelInfo]:
        return await self._provider.list_models()

    async def status(self) -> ProviderStatus:
        health = await self._provider.health()
        return ProviderStatus(
            provider=self._provider.name,
            models={tier: await self._resolver.resolve(tier) for tier in ModelTier},
            available=health.available,
            detail=health.detail,
        )

    async def model_settings(self) -> list[TierModelSettings]:
        return await self._resolver.describe()

    async def update_model_settings(
        self, changes: Mapping[ModelTier, str | None], *, allow_custom: bool
    ) -> list[TierModelSettings]:
        """Save model overrides; `None` removes an override and falls back to `.env`.

        Raises:
            InvalidInputError: a model is not offered by the provider and `allow_custom` is off.
        """
        to_save = {
            tier: (model.strip() or None) if model else None for tier, model in changes.items()
        }
        chosen = {model for model in to_save.values() if model is not None}
        if chosen and not allow_custom:
            known = {info.id for info in await self._provider.list_models()}
            unknown = sorted(chosen - known)
            if unknown:
                raise InvalidInputError(
                    f"Models not offered by {self._provider.name}: {', '.join(unknown)}",
                    user_message=(
                        f"Model {', '.join(unknown)} nie jest na liście dostępnych modeli. "
                        "Zaznacz „własny identyfikator”, jeśli chcesz go użyć mimo to."
                    ),
                )
        for tier, model in to_save.items():
            await self._resolver.set_override(tier, model)
        await self._session.commit()
        return await self._resolver.describe()

    async def test_model(self, *, tier: ModelTier | None, model: str | None) -> ModelTestResult:
        """Send a tiny prompt to a tier's model, or to an explicit model id."""
        target = model if model else await self._resolver.resolve(tier or ModelTier.MAIN)
        started = time.monotonic()
        try:
            result = await self._provider.complete(
                system=TEST_SYSTEM_PROMPT,
                messages=[ChatMessage(role="user", content="ping")],
                model=target,
            )
        except LLMError as exc:
            return ModelTestResult(
                ok=False, model=target, latency_ms=_elapsed_ms(started), detail=exc.user_message
            )
        return ModelTestResult(
            ok=True, model=result.model or target, latency_ms=_elapsed_ms(started), detail=None
        )


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def get_llm_provider(request: Request) -> LLMProvider:
    provider: LLMProvider = request.app.state.llm_provider
    return provider


def build_llm_service(
    provider: LLMProvider, settings: Settings, session: AsyncSession
) -> LLMService:
    resolver = ModelResolver(
        provider.name, settings.model_defaults(provider.name), AppSettingRepository(session)
    )
    return LLMService(provider, resolver, session)


def get_llm_service(
    session: SessionDep,
    settings: SettingsDep,
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> LLMService:
    return build_llm_service(provider, settings, session)


LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
