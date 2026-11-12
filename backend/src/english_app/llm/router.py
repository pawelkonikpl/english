"""HTTP API for the LLM layer: status, model list, model settings and a test call."""

from fastapi import APIRouter
from pydantic import BaseModel, model_validator

from english_app.llm.base import ModelTier
from english_app.llm.models import TierModelSettings
from english_app.llm.service import LLMServiceDep

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMStatusResponse(BaseModel):
    provider: str
    available: bool
    detail: str | None
    models: dict[ModelTier, str | None]


class ModelInfoResponse(BaseModel):
    id: str
    name: str
    source: str


class TierModelSettingsResponse(BaseModel):
    tier: ModelTier
    env_model: str | None
    override: str | None
    effective: str | None


class ModelSettingsResponse(BaseModel):
    provider: str
    tiers: list[TierModelSettingsResponse]


class ModelSettingsUpdate(BaseModel):
    """Fields left out stay unchanged; `null` removes the override for that tier."""

    main: str | None = None
    fast: str | None = None
    allow_custom: bool = False


class ModelTestRequest(BaseModel):
    tier: ModelTier | None = None
    model: str | None = None

    @model_validator(mode="after")
    def _one_target(self) -> "ModelTestRequest":
        if self.tier is not None and self.model:
            raise ValueError("Give either tier or model, not both")
        return self


class ModelTestResponse(BaseModel):
    ok: bool
    model: str | None
    latency_ms: int
    detail: str | None


def _settings_response(provider: str, tiers: list[TierModelSettings]) -> ModelSettingsResponse:
    return ModelSettingsResponse(
        provider=provider,
        tiers=[
            TierModelSettingsResponse(
                tier=t.tier, env_model=t.env_model, override=t.override, effective=t.effective
            )
            for t in tiers
        ],
    )


@router.get("/status", response_model=LLMStatusResponse)
async def get_status(llm: LLMServiceDep) -> LLMStatusResponse:
    status = await llm.status()
    return LLMStatusResponse(
        provider=status.provider,
        available=status.available,
        detail=status.detail,
        models=status.models,
    )


@router.get("/models", response_model=list[ModelInfoResponse])
async def get_models(llm: LLMServiceDep) -> list[ModelInfoResponse]:
    return [
        ModelInfoResponse(id=m.id, name=m.name, source=m.source) for m in await llm.list_models()
    ]


@router.get("/settings", response_model=ModelSettingsResponse)
async def get_model_settings(llm: LLMServiceDep) -> ModelSettingsResponse:
    return _settings_response(llm.provider_name, await llm.model_settings())


@router.put("/settings", response_model=ModelSettingsResponse)
async def update_model_settings(
    payload: ModelSettingsUpdate, llm: LLMServiceDep
) -> ModelSettingsResponse:
    changes = {
        ModelTier(field): getattr(payload, field)
        for field in ("main", "fast")
        if field in payload.model_fields_set
    }
    tiers = await llm.update_model_settings(changes, allow_custom=payload.allow_custom)
    return _settings_response(llm.provider_name, tiers)


@router.post("/test", response_model=ModelTestResponse)
async def test_model(payload: ModelTestRequest, llm: LLMServiceDep) -> ModelTestResponse:
    result = await llm.test_model(tier=payload.tier, model=payload.model)
    return ModelTestResponse(
        ok=result.ok, model=result.model, latency_ms=result.latency_ms, detail=result.detail
    )
