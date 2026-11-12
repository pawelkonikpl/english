import pytest
from fastapi import APIRouter

from english_app.core.config import Settings
from english_app.core.errors import ConfigurationError
from english_app.core.modules import AppModule, resolve_enabled_modules
from english_app.llm.factory import PROVIDER_FACTORIES, create_llm_provider
from english_app.llm.providers.claude_code import ClaudeCodeProvider
from english_app.llm.providers.copilot import CopilotProvider
from english_app.llm.providers.fake import FakeProvider


def module(key: str, *deps: str) -> AppModule:
    return AppModule(key=key, title=key, router=APIRouter(), depends_on=deps)


AVAILABLE = [module("b", "a"), module("a"), module("c", "b")]


def test_empty_list_enables_every_module_with_dependencies_first() -> None:
    keys = [m.key for m in resolve_enabled_modules(AVAILABLE, [])]

    assert sorted(keys) == ["a", "b", "c"]
    assert keys.index("a") < keys.index("b") < keys.index("c")


def test_only_listed_modules_are_enabled() -> None:
    assert [m.key for m in resolve_enabled_modules(AVAILABLE, ["a"])] == ["a"]


def test_unknown_module_stops_startup() -> None:
    with pytest.raises(ConfigurationError, match=r"Unknown modules.*nope"):
        resolve_enabled_modules(AVAILABLE, ["a", "nope"])


def test_missing_dependency_stops_startup() -> None:
    with pytest.raises(ConfigurationError, match=r"'c' requires b"):
        resolve_enabled_modules(AVAILABLE, ["a", "c"])


def settings(provider: str) -> Settings:
    return Settings(_env_file=None, llm_provider=provider)  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("name", "expected"),
    [("fake", FakeProvider), ("claude_code", ClaudeCodeProvider), ("copilot", CopilotProvider)],
)
def test_factory_builds_the_configured_provider(name: str, expected: type) -> None:
    provider = create_llm_provider(settings(name))

    assert isinstance(provider, expected)
    assert provider.name == name


def test_unknown_provider_lists_available_ones() -> None:
    with pytest.raises(ConfigurationError) as error:
        create_llm_provider(settings("gpt"))

    assert all(name in str(error.value) for name in PROVIDER_FACTORIES)


def test_comma_separated_settings_are_split_and_blank_models_are_none() -> None:
    parsed = Settings(  # type: ignore[call-arg]
        _env_file=None,
        enabled_modules=" profile, review ,",
        claude_code_models="a,b",
        copilot_model="  ",
    )

    assert parsed.enabled_modules == ["profile", "review"]
    assert parsed.claude_code_models == ["a", "b"]
    assert parsed.copilot_model is None
