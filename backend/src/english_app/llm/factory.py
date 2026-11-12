"""Creates the LLM provider selected by `LLM_PROVIDER`.

Adding a provider means writing one `LLMProvider` subclass and one entry in
`PROVIDER_FACTORIES`. SDK imports happen inside the factories, so a provider's SDK is
only loaded when that provider is selected.
"""

from collections.abc import Callable

from english_app.core.config import Settings
from english_app.core.errors import ConfigurationError
from english_app.llm.base import LLMProvider

ProviderFactory = Callable[[Settings], LLMProvider]


def _create_claude_code(settings: Settings) -> LLMProvider:
    from english_app.llm.providers.claude_code import ClaudeCodeProvider

    return ClaudeCodeProvider(
        model_catalog=settings.claude_code_models,
        timeout_seconds=settings.llm_timeout_seconds,
        cli_path=settings.claude_code_cli_path,
    )


def _create_copilot(settings: Settings) -> LLMProvider:
    from english_app.llm.providers.copilot import CopilotProvider

    return CopilotProvider(timeout_seconds=settings.llm_timeout_seconds)


def _create_fake(settings: Settings) -> LLMProvider:
    from english_app.llm.providers.fake import FakeProvider

    return FakeProvider()


PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "claude_code": _create_claude_code,
    "copilot": _create_copilot,
    "fake": _create_fake,
}


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Instantiate the configured provider.

    Raises:
        ConfigurationError: `LLM_PROVIDER` names a provider that does not exist.
    """
    factory = PROVIDER_FACTORIES.get(settings.llm_provider)
    if factory is None:
        raise ConfigurationError(
            f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
            f"Available: {', '.join(PROVIDER_FACTORIES)}"
        )
    return factory(settings)
