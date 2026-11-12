"""Claude Code provider: runs the user's logged-in Claude Code through `claude-agent-sdk`.

The SDK drives a full coding agent, so every call disables all built-in tools, ignores
user/project settings and runs in an empty temporary directory: the model can only talk.
"""

import asyncio
import logging
import shutil
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import claude_agent_sdk
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    ResultMessage,
    query,
)
from pydantic import ValidationError

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

_AUTH_STATUS_CODES = {401, 403}
_RATE_LIMIT_STATUS = 429
_AUTH_HINTS = ("login", "log in", "authenticat", "unauthorized", "api key")

CLI_NOT_FOUND_HELP = (
    "Nie znaleziono Claude Code CLI. Zainstaluj Claude Code albo ustaw CLAUDE_CODE_CLI_PATH."
)
LOGIN_HELP = "Zaloguj się w Claude Code poleceniem `claude` (a potem /login) i spróbuj ponownie."


class ClaudeCodeProvider(LLMProvider):
    name: ClassVar[str] = "claude_code"

    def __init__(
        self, *, model_catalog: Sequence[str], timeout_seconds: float, cli_path: str | None
    ):
        self._model_catalog = list(model_catalog)
        self._timeout_seconds = timeout_seconds
        self._cli_path = cli_path
        self._workdir = Path(tempfile.mkdtemp(prefix="english-app-claude-"))
        self._last_unavailable: str | None = None

    async def complete(
        self, *, system: str, messages: Sequence[ChatMessage], model: str | None
    ) -> LLMResult[str]:
        result = await self._run(system=system, prompt=render_prompt(messages), model=model)
        if not result.result:
            raise LLMOutputError("Claude Code returned an empty reply")
        return LLMResult(value=result.result, model=_answering_model(result, model))

    async def complete_structured(
        self,
        *,
        system: str,
        messages: Sequence[ChatMessage],
        schema: type[SchemaT],
        model: str | None,
    ) -> LLMResult[SchemaT]:
        prompt = render_prompt(messages)
        output_format = {"type": "json_schema", "schema": schema.model_json_schema()}
        result = await self._run(
            system=system, prompt=prompt, model=model, output_format=output_format
        )
        try:
            value = _validate_native(result, schema)
        except LLMOutputError as first_error:
            # One retry in plain-text JSON mode, telling the model what was wrong.
            logger.info("Retrying structured output for %s: %s", schema.__name__, first_error)
            retry = await self._run(
                system=f"{system}\n\n{schema_instruction(schema)}",
                prompt=f"{prompt}\n\n{validation_feedback(first_error)}",
                model=model,
            )
            value = parse_structured(retry.result or "", schema)
            return LLMResult(value=value, model=_answering_model(retry, model))
        return LLMResult(value=value, model=_answering_model(result, model))

    async def list_models(self) -> list[ModelInfo]:
        # The SDK has no model listing, so the catalog comes from configuration.
        return [
            ModelInfo(id=model_id, name=model_id, source="config")
            for model_id in self._model_catalog
        ]

    async def health(self) -> ProviderHealth:
        if not self._cli_available():
            return ProviderHealth(
                available=False,
                detail=CLI_NOT_FOUND_HELP,
            )
        if self._last_unavailable is not None:
            return ProviderHealth(available=False, detail=self._last_unavailable)
        return ProviderHealth(available=True)

    async def aclose(self) -> None:
        shutil.rmtree(self._workdir, ignore_errors=True)

    async def _run(
        self,
        *,
        system: str,
        prompt: str,
        model: str | None,
        output_format: dict[str, Any] | None = None,
    ) -> ResultMessage:
        options = ClaudeAgentOptions(
            system_prompt=system,
            model=model,
            tools=[],
            setting_sources=[],
            cwd=self._workdir,
            cli_path=self._cli_path,
            output_format=output_format,
            # Plain replies need one turn; structured output may need an extra internal turn.
            max_turns=1 if output_format is None else 3,
        )
        started = time.monotonic()
        try:
            async with asyncio.timeout(self._timeout_seconds):
                result = await _collect_result(prompt, options)
        except TimeoutError as exc:
            raise LLMTimeoutError(
                f"Claude Code did not answer in {self._timeout_seconds}s"
            ) from exc
        except CLINotFoundError as exc:
            raise self._unavailable(
                "Claude Code CLI not found",
                CLI_NOT_FOUND_HELP,
            ) from exc
        except ProcessError as exc:
            if _looks_like_auth_problem(exc.stderr or str(exc)):
                raise self._unavailable("Claude Code is not logged in", LOGIN_HELP) from exc
            raise LLMError(f"Claude Code process failed with exit code {exc.exit_code}") from exc
        except ClaudeSDKError as exc:
            raise LLMError(f"Claude Code SDK error: {type(exc).__name__}") from exc
        finally:
            logger.info(
                "claude_code call model=%s structured=%s duration_ms=%d",
                model,
                output_format is not None,
                (time.monotonic() - started) * 1000,
            )

        self._raise_for_result_error(result)
        self._last_unavailable = None
        return result

    def _raise_for_result_error(self, result: ResultMessage) -> None:
        if not result.is_error:
            return
        status = result.api_error_status
        errors = "; ".join(result.errors or []) or result.subtype
        if status in _AUTH_STATUS_CODES or _looks_like_auth_problem(errors):
            raise self._unavailable(f"Claude Code is not authorized (status {status})", LOGIN_HELP)
        if status == _RATE_LIMIT_STATUS:
            raise LLMError(
                "Claude Code hit a rate limit",
                user_message="Osiągnięto limit zapytań w subskrypcji Claude. Spróbuj później.",
            )
        raise LLMError(f"Claude Code returned an error result: {result.subtype} (status {status})")

    def _unavailable(self, message: str, user_message: str) -> LLMUnavailableError:
        self._last_unavailable = user_message
        return LLMUnavailableError(message, user_message=user_message)

    def _cli_available(self) -> bool:
        if self._cli_path:
            return Path(self._cli_path).exists()
        bundled = Path(claude_agent_sdk.__file__).parent / "_bundled" / "claude"
        return bundled.exists() or shutil.which("claude") is not None


async def _collect_result(prompt: str, options: ClaudeAgentOptions) -> ResultMessage:
    result: ResultMessage | None = None
    # Consume the whole stream: stopping early would leave the CLI process running.
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            result = message
    if result is None:
        raise LLMOutputError("Claude Code finished without a result message")
    return result


def _validate_native(result: ResultMessage, schema: type[SchemaT]) -> SchemaT:
    if result.structured_output is not None:
        try:
            return schema.model_validate(result.structured_output)
        except ValidationError as exc:
            raise LLMOutputError(
                f"Structured output does not match {schema.__name__}: {exc}"
            ) from exc
    return parse_structured(result.result or "", schema)


def _answering_model(result: ResultMessage, requested: str | None) -> str | None:
    if result.model_usage:
        return next(iter(result.model_usage))
    return requested


def _looks_like_auth_problem(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in _AUTH_HINTS)
