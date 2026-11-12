from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from claude_agent_sdk import ClaudeAgentOptions, CLINotFoundError, ProcessError, ResultMessage
from pydantic import BaseModel

from english_app.llm.base import (
    ChatMessage,
    LLMOutputError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from english_app.llm.providers import claude_code
from english_app.llm.providers.claude_code import ClaudeCodeProvider

USER = [ChatMessage(role="user", content="Hello")]


class Reply(BaseModel):
    text: str


def result(**overrides: Any) -> ResultMessage:
    fields: dict[str, Any] = {
        "subtype": "success",
        "duration_ms": 10,
        "duration_api_ms": 8,
        "is_error": False,
        "num_turns": 1,
        "session_id": "s",
        "result": "Hi!",
        "model_usage": {"claude-opus-5-5": {}},
    }
    fields.update(overrides)
    return ResultMessage(**fields)


class FakeQuery:
    """Replaces claude_agent_sdk.query and records the options of every call."""

    def __init__(self, *outcomes: ResultMessage | Exception) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[tuple[str, ClaudeAgentOptions]] = []

    def __call__(self, *, prompt: str, options: ClaudeAgentOptions) -> AsyncIterator[Any]:
        self.calls.append((prompt, options))
        outcome = self.outcomes.pop(0)

        async def stream() -> AsyncIterator[Any]:
            if isinstance(outcome, Exception):
                raise outcome
            yield object()  # other message types are ignored
            yield outcome

        return stream()


@pytest.fixture
def provider() -> ClaudeCodeProvider:
    return ClaudeCodeProvider(model_catalog=["a", "b"], timeout_seconds=5, cli_path=None)


def install(monkeypatch: pytest.MonkeyPatch, fake: FakeQuery) -> FakeQuery:
    monkeypatch.setattr(claude_code, "query", fake)
    return fake


async def test_plain_reply_and_answering_model(provider, monkeypatch) -> None:
    fake = install(monkeypatch, FakeQuery(result()))

    reply = await provider.complete(system="Be nice", messages=USER, model="claude-opus-5-5")

    assert (reply.value, reply.model) == ("Hi!", "claude-opus-5-5")
    prompt, options = fake.calls[0]
    assert prompt == "Hello"
    assert options.system_prompt == "Be nice"
    assert options.model == "claude-opus-5-5"


async def test_model_runs_without_tools_settings_or_project_files(provider, monkeypatch) -> None:
    fake = install(monkeypatch, FakeQuery(result(), result(structured_output={"text": "x"})))

    await provider.complete(system="s", messages=USER, model=None)
    await provider.complete_structured(system="s", messages=USER, schema=Reply, model=None)

    for _, options in fake.calls:
        assert options.tools == []
        assert options.setting_sources == []
        workdir = Path(str(options.cwd))
        assert workdir.name.startswith("english-app-claude-")
        assert list(workdir.iterdir()) == []


async def test_structured_output_uses_native_json_schema(provider, monkeypatch) -> None:
    fake = install(monkeypatch, FakeQuery(result(structured_output={"text": "ok"})))

    reply = await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")

    assert reply.value == Reply(text="ok")
    assert fake.calls[0][1].output_format == {
        "type": "json_schema",
        "schema": Reply.model_json_schema(),
    }


async def test_invalid_structured_output_is_retried_once_in_text_mode(
    provider, monkeypatch
) -> None:
    fake = install(
        monkeypatch,
        FakeQuery(result(structured_output={"wrong": 1}), result(result='{"text": "fixed"}')),
    )

    reply = await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")

    assert reply.value == Reply(text="fixed")
    retry_prompt, retry_options = fake.calls[1]
    assert "previous reply was not valid JSON" in retry_prompt
    assert retry_options.output_format is None
    assert "JSON Schema" in str(retry_options.system_prompt)


async def test_second_invalid_reply_raises_output_error(provider, monkeypatch) -> None:
    install(
        monkeypatch,
        FakeQuery(result(structured_output=None, result="nope"), result(result="still nope")),
    )

    with pytest.raises(LLMOutputError):
        await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")


async def test_missing_cli_makes_provider_unavailable(provider, monkeypatch) -> None:
    install(monkeypatch, FakeQuery(CLINotFoundError("no cli")))

    with pytest.raises(LLMUnavailableError) as error:
        await provider.complete(system="s", messages=USER, model=None)

    assert "Claude Code" in error.value.user_message


async def test_auth_error_result_is_reported_in_health_until_next_success(
    provider, monkeypatch
) -> None:
    install(
        monkeypatch,
        FakeQuery(result(is_error=True, api_error_status=401, result=None), result()),
    )

    with pytest.raises(LLMUnavailableError):
        await provider.complete(system="s", messages=USER, model=None)
    unhealthy = await provider.health()
    await provider.complete(system="s", messages=USER, model=None)
    healthy = await provider.health()

    assert unhealthy.available is False and "Zaloguj" in (unhealthy.detail or "")
    assert healthy.available is True


async def test_login_hint_in_process_error_means_unavailable(provider, monkeypatch) -> None:
    install(monkeypatch, FakeQuery(ProcessError("failed", exit_code=1, stderr="Please run /login")))

    with pytest.raises(LLMUnavailableError):
        await provider.complete(system="s", messages=USER, model=None)


async def test_slow_cli_times_out(monkeypatch) -> None:
    provider = ClaudeCodeProvider(model_catalog=[], timeout_seconds=0.05, cli_path=None)

    def slow_query(*, prompt: str, options: ClaudeAgentOptions) -> AsyncIterator[Any]:
        async def stream() -> AsyncIterator[Any]:
            import asyncio

            await asyncio.sleep(1)
            yield result()

        return stream()

    monkeypatch.setattr(claude_code, "query", slow_query)

    with pytest.raises(LLMTimeoutError):
        await provider.complete(system="s", messages=USER, model=None)


async def test_models_come_from_configuration(provider) -> None:
    models = await provider.list_models()

    assert [(m.id, m.source) for m in models] == [("a", "config"), ("b", "config")]


async def test_message_content_is_not_logged(provider, monkeypatch, caplog) -> None:
    install(monkeypatch, FakeQuery(result(result="SECRET-REPLY")))
    caplog.set_level("DEBUG")

    await provider.complete(
        system="s", messages=[ChatMessage(role="user", content="SECRET-INPUT")], model=None
    )

    assert "SECRET" not in caplog.text
    assert "claude_code call" in caplog.text
