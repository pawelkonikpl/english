from dataclasses import dataclass
from typing import Any, ClassVar

import pytest
from copilot.rpc import PermissionDecisionReject
from pydantic import BaseModel

from english_app.llm.base import ChatMessage, LLMError, LLMOutputError, LLMUnavailableError
from english_app.llm.providers import copilot as copilot_module
from english_app.llm.providers.copilot import CopilotProvider

USER = [ChatMessage(role="user", content="Hello")]


class Reply(BaseModel):
    text: str


@dataclass
class Data:
    content: str
    model: str | None = "gpt-test"


@dataclass
class Event:
    data: Data


@dataclass
class Auth:
    isAuthenticated: bool
    login: str | None = "octocat"


@dataclass
class Model:
    id: str
    name: str


class FakeSession:
    def __init__(self, client: "FakeClient") -> None:
        self.client = client
        self.disconnected = False

    async def send_and_wait(self, prompt: str, timeout: float) -> Event:
        self.client.prompts.append(prompt)
        outcome = self.client.text_replies.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return Event(Data(outcome))

    async def send_and_wait_typed(self, prompt: str, response_type: type, timeout: float) -> Any:
        self.client.prompts.append(prompt)
        outcome = self.client.typed_replies.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return response_type.model_validate(outcome)

    async def disconnect(self) -> None:
        self.disconnected = True


class FakeClient:
    instances: ClassVar[list["FakeClient"]] = []

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.sessions: list[tuple[dict[str, Any], FakeSession]] = []
        self.prompts: list[str] = []
        self.text_replies: list[Any] = []
        self.typed_replies: list[Any] = []
        self.models = [Model("gpt-a", "GPT A")]
        self.list_calls = 0
        self.authenticated = True
        self.started = self.stopped = False
        FakeClient.instances.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def create_session(self, **kwargs: Any) -> FakeSession:
        session = FakeSession(self)
        self.sessions.append((kwargs, session))
        return session

    async def list_models(self) -> list[Model]:
        self.list_calls += 1
        return self.models

    async def get_auth_status(self) -> Auth:
        return Auth(isAuthenticated=self.authenticated)


@pytest.fixture
def provider(monkeypatch: pytest.MonkeyPatch) -> CopilotProvider:
    FakeClient.instances.clear()
    monkeypatch.setattr(copilot_module, "CopilotClient", FakeClient)
    return CopilotProvider(timeout_seconds=5)


async def client_of(provider: CopilotProvider) -> FakeClient:
    await provider.health()  # starts the client
    return FakeClient.instances[-1]


async def test_sessions_have_no_tools_deny_permissions_and_replace_the_system_prompt(
    provider,
) -> None:
    client = await client_of(provider)
    client.text_replies.append("Hi!")

    reply = await provider.complete(system="Be a barista", messages=USER, model="gpt-a")

    kwargs, session = client.sessions[0]
    assert reply.value == "Hi!" and reply.model == "gpt-test"
    assert kwargs["available_tools"] == []
    assert kwargs["system_message"] == {"mode": "replace", "content": "Be a barista"}
    assert kwargs["model"] == "gpt-a"
    assert kwargs["working_directory"] == client.kwargs["working_directory"]
    decision = kwargs["on_permission_request"](object(), {})
    assert isinstance(decision, PermissionDecisionReject)
    assert session.disconnected


async def test_structured_reply_uses_the_typed_helper(provider) -> None:
    client = await client_of(provider)
    client.typed_replies.append({"text": "ok"})

    reply = await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")

    assert reply.value == Reply(text="ok")


async def test_invalid_typed_reply_is_retried_once_in_text_mode(provider) -> None:
    client = await client_of(provider)
    client.typed_replies.append({"wrong": 1})
    client.text_replies.append('```json\n{"text": "fixed"}\n```')

    reply = await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")

    assert reply.value == Reply(text="fixed")
    assert "previous reply was not valid JSON" in client.prompts[-1]


async def test_second_invalid_reply_raises_output_error(provider) -> None:
    client = await client_of(provider)
    client.typed_replies.append({"wrong": 1})
    client.text_replies.append("no json")

    with pytest.raises(LLMOutputError):
        await provider.complete_structured(system="s", messages=USER, schema=Reply, model="m")


async def test_auth_failure_makes_provider_unavailable(provider) -> None:
    client = await client_of(provider)
    client.text_replies.append(RuntimeError("Not authenticated. Please authenticate first."))

    with pytest.raises(LLMUnavailableError):
        await provider.complete(system="s", messages=USER, model=None)
    assert (await provider.health()).available is False


async def test_unknown_model_gets_a_clear_message(provider) -> None:
    client = await client_of(provider)
    client.text_replies.append(RuntimeError("model 'x' is not supported"))

    with pytest.raises(LLMError) as error:
        await provider.complete(system="s", messages=USER, model="x")

    assert "subskrypcji" in error.value.user_message


async def test_health_reports_missing_login(provider) -> None:
    client = await client_of(provider)
    client.authenticated = False

    health = await provider.health()

    assert health.available is False and "COPILOT_GITHUB_TOKEN" in (health.detail or "")


async def test_model_list_comes_from_the_sdk_and_is_cached(provider) -> None:
    client = await client_of(provider)

    first = await provider.list_models()
    await provider.list_models()

    assert [(m.id, m.name, m.source) for m in first] == [("gpt-a", "GPT A", "provider")]
    assert client.list_calls == 1


async def test_client_is_stopped_on_shutdown(provider) -> None:
    client = await client_of(provider)

    await provider.aclose()

    assert client.stopped
