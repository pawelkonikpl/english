"""GitHub Copilot provider: runs the user's Copilot subscription through `github-copilot-sdk`.

Each call opens a fresh session with no tools, a replaced system prompt and an empty
working directory, and denies every permission request: the model can only talk.
"""

import asyncio
import logging
import shutil
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from copilot import CopilotClient
from copilot.rpc import PermissionDecisionReject

from english_app.llm.base import (
    ChatMessage,
    LLMError,
    LLMOutputError,
    LLMProvider,
    LLMResult,
    LLMTimeoutError,
    LLMUnavailableError,
    ModelInfo,
    ProviderHealth,
    SchemaT,
)
from english_app.llm.structured import (
    parse_structured,
    render_prompt,
    schema_instruction,
    validation_feedback,
)

logger = logging.getLogger(__name__)

MODELS_CACHE_SECONDS = 600
LOGIN_HELP = (
    "Zaloguj się do GitHub Copilot (np. poleceniem `copilot` i /login) "
    "albo ustaw COPILOT_GITHUB_TOKEN, a potem spróbuj ponownie."
)
START_HELP = (
    "Nie udało się uruchomić GitHub Copilot. Pobierz runtime poleceniem "
    "`python -m copilot download-runtime` i sprawdź logowanie."
)


def _is_auth_problem(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(hint in message for hint in ("authenticat", "login", "unauthorized", "401"))


def _deny_all_permissions(request: Any, invocation: Any) -> PermissionDecisionReject:
    return PermissionDecisionReject(feedback="Tools are disabled in this application.")


class CopilotProvider(LLMProvider):
    name: ClassVar[str] = "copilot"

    def __init__(self, *, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds
        self._workdir = Path(tempfile.mkdtemp(prefix="english-app-copilot-"))
        self._client: CopilotClient | None = None
        self._client_lock = asyncio.Lock()
        self._models_cache: tuple[float, list[ModelInfo]] | None = None
        self._last_unavailable: str | None = None

    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> LLMResult[str]:
        content, answered_by = await self._send_text(system, render_prompt(messages), model)
        return LLMResult(value=content, model=answered_by or model)

    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        model: str | None,
    ) -> LLMResult[SchemaT]:
        prompt = render_prompt(messages)

        async def send_typed(session: Any) -> SchemaT:
            try:
                typed: SchemaT = await session.send_and_wait_typed(
                    prompt, response_type=schema, timeout=self._timeout_seconds
                )
            except (ValueError, TypeError) as exc:  # the typed helper's validation failure
                raise LLMOutputError(f"Copilot reply does not match {schema.__name__}") from exc
            return typed

        try:
            value = await self._call(model, system, send_typed)
            return LLMResult(value=value, model=model)
        except LLMOutputError as first_error:
            logger.info("Retrying structured output for %s: %s", schema.__name__, first_error)
            retry_error = first_error

        content, answered_by = await self._send_text(
            f"{system}\n\n{schema_instruction(schema)}",
            f"{prompt}\n\n{validation_feedback(retry_error)}",
            model,
        )
        return LLMResult(value=parse_structured(content, schema), model=answered_by or model)

    async def list_models(self) -> list[ModelInfo]:
        now = time.monotonic()
        if self._models_cache is not None and now - self._models_cache[0] < MODELS_CACHE_SECONDS:
            return self._models_cache[1]
        client = await self._get_client()
        try:
            models = await client.list_models()
        except Exception as exc:  # SDK boundary: any failure means "cannot list models"
            if _is_auth_problem(exc):
                self._last_unavailable = LOGIN_HELP
                raise LLMUnavailableError(
                    "Copilot is not authorized", user_message=LOGIN_HELP
                ) from exc
            raise LLMError("Copilot model listing failed") from exc
        infos = [ModelInfo(id=m.id, name=m.name or m.id, source="provider") for m in models]
        self._models_cache = (now, infos)
        return infos

    async def health(self) -> ProviderHealth:
        try:
            client = await self._get_client()
            status = await client.get_auth_status()
        except LLMUnavailableError as exc:
            return ProviderHealth(available=False, detail=exc.user_message)
        except Exception:  # SDK boundary: report instead of failing the status endpoint
            logger.exception("Copilot health check failed")
            return ProviderHealth(available=False, detail=START_HELP)
        if not status.isAuthenticated:
            return ProviderHealth(available=False, detail=LOGIN_HELP)
        if self._last_unavailable is not None:
            return ProviderHealth(available=False, detail=self._last_unavailable)
        return ProviderHealth(
            available=True, detail=f"Zalogowano jako {status.login}" if status.login else None
        )

    async def aclose(self) -> None:
        if self._client is not None:
            try:
                await self._client.stop()
            except Exception:  # shutdown must not fail because of the SDK
                logger.exception("Stopping Copilot client failed")
            self._client = None
        shutil.rmtree(self._workdir, ignore_errors=True)

    async def _send_text(
        self, system: str, prompt: str, model: str | None
    ) -> tuple[str, str | None]:
        event = await self._call(
            model,
            system,
            lambda session: session.send_and_wait(prompt, timeout=self._timeout_seconds),
        )
        data = getattr(event, "data", None)
        content = getattr(data, "content", None)
        if not content:
            raise LLMOutputError("Copilot returned no assistant message")
        return str(content), getattr(data, "model", None)

    async def _call(self, model: str | None, system: str, send: Any) -> Any:
        client = await self._get_client()
        started = time.monotonic()
        try:
            session = await client.create_session(
                model=model,
                system_message={"mode": "replace", "content": system},
                available_tools=[],
                on_permission_request=_deny_all_permissions,
                working_directory=str(self._workdir),
                skip_custom_instructions=True,
            )
            try:
                result = await send(session)
            finally:
                await session.disconnect()
        except TimeoutError as exc:
            raise LLMTimeoutError(f"Copilot did not answer in {self._timeout_seconds}s") from exc
        except LLMError:
            raise
        except Exception as exc:  # SDK boundary: unknown runtime/RPC failures
            if _is_auth_problem(exc):
                self._last_unavailable = LOGIN_HELP
                raise LLMUnavailableError(
                    "Copilot is not authorized", user_message=LOGIN_HELP
                ) from exc
            if "model" in str(exc).lower():
                raise LLMError(
                    f"Copilot rejected model {model!r}",
                    user_message="Wybrany model nie jest dostępny w Twojej subskrypcji Copilot.",
                ) from exc
            raise LLMError(f"Copilot call failed: {type(exc).__name__}") from exc
        finally:
            logger.info(
                "copilot call model=%s duration_ms=%d", model, (time.monotonic() - started) * 1000
            )
        self._last_unavailable = None
        return result

    async def _get_client(self) -> CopilotClient:
        async with self._client_lock:
            if self._client is not None:
                return self._client
            client = CopilotClient(working_directory=str(self._workdir), log_level="error")
            try:
                await client.start()
            except Exception as exc:  # SDK boundary: runtime missing or failed to start
                self._last_unavailable = START_HELP
                raise LLMUnavailableError(
                    "Copilot runtime failed to start", user_message=START_HELP
                ) from exc
            self._client = client
            return client
