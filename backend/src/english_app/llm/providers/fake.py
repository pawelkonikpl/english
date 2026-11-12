"""Deterministic provider for tests, offline work and UI demos. Never calls a network."""

from collections.abc import Callable, Sequence
from typing import Any, ClassVar

from pydantic import BaseModel

from english_app.llm.base import (
    ChatMessage,
    LLMProvider,
    LLMResult,
    ModelInfo,
    ProviderHealth,
    SchemaT,
)

DEFAULT_MODEL = "fake-main"
FAKE_MODELS = ("fake-main", "fake-fast")

CannedFactory = Callable[[Sequence[ChatMessage]], BaseModel]


class FakeProvider(LLMProvider):
    name: ClassVar[str] = "fake"

    def __init__(self) -> None:
        self._canned: dict[type[BaseModel], CannedFactory] = {}

    def register(self, schema: type[BaseModel], factory: CannedFactory) -> None:
        """Use `factory` to build replies for `schema` instead of generated placeholders."""
        self._canned[schema] = factory

    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> LLMResult[str]:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        reply = f'That\'s interesting! You said: "{last_user}". Tell me more.'
        return LLMResult(value=reply, model=model or DEFAULT_MODEL)

    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        model: str | None,
    ) -> LLMResult[SchemaT]:
        factory = self._canned.get(schema)
        if factory is not None:
            value = schema.model_validate(factory(messages).model_dump())
        else:
            value = schema.model_validate(sample_from_schema(schema.model_json_schema()))
        return LLMResult(value=value, model=model or DEFAULT_MODEL)

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id=model_id, name=model_id, source="provider") for model_id in FAKE_MODELS
        ]

    async def health(self) -> ProviderHealth:
        return ProviderHealth(available=True, detail="Provider testowy: odpowiedzi są przykładowe.")


def sample_from_schema(schema: dict[str, Any]) -> Any:
    """Build a minimal value that validates against a Pydantic-generated JSON Schema."""
    definitions: dict[str, Any] = schema.get("$defs", {})
    return _sample(schema, definitions)


def _sample(node: dict[str, Any], definitions: dict[str, Any]) -> Any:
    if "$ref" in node:
        return _sample(definitions[node["$ref"].rsplit("/", 1)[-1]], definitions)
    if "default" in node:
        return node["default"]
    if "const" in node:
        return node["const"]
    if "enum" in node:
        return node["enum"][0]
    for combinator in ("anyOf", "oneOf", "allOf"):
        if combinator in node:
            options = [opt for opt in node[combinator] if opt.get("type") != "null"]
            return _sample(options[0] if options else node[combinator][0], definitions)

    node_type = node.get("type")
    if node_type == "object":
        properties: dict[str, Any] = node.get("properties", {})
        return {name: _sample(prop, definitions) for name, prop in properties.items()}
    if node_type == "array":
        count = max(node.get("minItems", 1), 1)
        return [_sample(node.get("items", {}), definitions) for _ in range(count)]
    if node_type == "string":
        return "example"
    if node_type == "integer":
        return int(node.get("minimum", 0))
    if node_type == "number":
        return float(node.get("minimum", 0))
    if node_type == "boolean":
        return True
    return None
