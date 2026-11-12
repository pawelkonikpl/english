"""The contract every LLM provider implements, plus shared value types and errors."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar, Generic, Literal, TypeVar

from pydantic import BaseModel

from english_app.core.errors import AppError

SchemaT = TypeVar("SchemaT", bound=BaseModel)
ValueT = TypeVar("ValueT")


class ModelTier(StrEnum):
    """Which configured model a task should use."""

    MAIN = "main"  # conversation replies, lesson generation, summaries
    FAST = "fast"  # sentence checks, hints, phrase explanations


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True)
class ModelInfo:
    id: str
    name: str
    source: Literal["provider", "config"]


@dataclass(frozen=True)
class LLMResult(Generic[ValueT]):
    value: ValueT
    model: str | None
    """The model that answered, if the SDK reports it; otherwise the requested model."""


@dataclass(frozen=True)
class ProviderHealth:
    available: bool
    detail: str | None = None
    """Polish message for the user when the provider is not available."""


class LLMError(AppError):
    status_code = 502
    code = "llm_error"
    default_user_message = "Model AI zwrócił błąd. Spróbuj ponownie za chwilę."


class LLMUnavailableError(LLMError):
    status_code = 503
    code = "llm_unavailable"
    default_user_message = (
        "Model AI jest niedostępny. Sprawdź, czy wybrany provider jest zainstalowany i zalogowany."
    )


class LLMTimeoutError(LLMError):
    status_code = 504
    code = "llm_timeout"
    default_user_message = "Model AI nie odpowiedział na czas. Spróbuj ponownie."


class LLMOutputError(LLMError):
    status_code = 502
    code = "llm_invalid_output"
    default_user_message = "Model AI zwrócił odpowiedź w nieoczekiwanym formacie. Spróbuj ponownie."


class LLMProvider(ABC):
    """A language model backend. Providers are stateless: every call gets the full history."""

    name: ClassVar[str]

    @abstractmethod
    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> LLMResult[str]:
        """Return a plain-text reply to the last user message."""

    @abstractmethod
    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        model: str | None,
    ) -> LLMResult[SchemaT]:
        """Return a reply validated against `schema`.

        Raises:
            LLMOutputError: the reply could not be turned into a valid `schema` instance.
        """

    async def stream(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> AsyncIterator[str]:
        """Yield the reply in chunks. Default: one chunk with the complete reply."""
        result = await self.complete(system=system, messages=messages, model=model)
        yield result.value

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Models the user can choose from in the settings screen."""

    @abstractmethod
    async def health(self) -> ProviderHealth:
        """Cheap availability check that does not call the model."""

    async def aclose(self) -> None:  # noqa: B027 - optional hook, most providers hold nothing
        """Release resources when the application shuts down."""
