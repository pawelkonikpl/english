"""Application settings read from the repository-level `.env` file."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/src/english_app/core/config.py -> repository root is four levels up.
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATABASE_PATH = REPO_ROOT / "data" / "english.db"
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

CommaSeparated = Annotated[list[str], NoDecode]


@dataclass(frozen=True)
class ProviderModelDefaults:
    """Models configured in `.env` for one LLM provider."""

    main: str | None
    fast: str | None
    catalog: list[str]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider
    llm_provider: str = "claude_code"
    llm_timeout_seconds: float = 90.0

    # LLM models per provider (empty means "let the provider decide")
    claude_code_model: str | None = "claude-opus-5-5"
    claude_code_model_fast: str | None = "claude-haiku-5-5"
    claude_code_models: CommaSeparated = [
        "claude-opus-5-5",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
    ]
    claude_code_cli_path: str | None = None
    copilot_model: str | None = None
    copilot_model_fast: str | None = None

    # Application
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DATABASE_PATH}"
    enabled_modules: CommaSeparated = []
    app_timezone: str = "Europe/Warsaw"
    daily_new_phrases: int = 10
    host: str = "127.0.0.1"
    port: int = 8000

    @field_validator("claude_code_models", "enabled_modules", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "claude_code_model",
        "claude_code_model_fast",
        "claude_code_cli_path",
        "copilot_model",
        "copilot_model_fast",
        mode="before",
    )
    @classmethod
    def _empty_string_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def model_defaults(self, provider: str) -> ProviderModelDefaults:
        """Return the `.env` model configuration for the given provider."""
        if provider == "claude_code":
            return ProviderModelDefaults(
                self.claude_code_model, self.claude_code_model_fast, self.claude_code_models
            )
        if provider == "copilot":
            return ProviderModelDefaults(self.copilot_model, self.copilot_model_fast, [])
        return ProviderModelDefaults(None, None, [])

    @property
    def sqlite_path(self) -> Path | None:
        """Filesystem path of the SQLite database, if the URL points to a file."""
        prefix = "sqlite+aiosqlite:///"
        if not self.database_url.startswith(prefix):
            return None
        raw_path = self.database_url.removeprefix(prefix)
        if not raw_path or raw_path == ":memory:":
            return None
        return Path(raw_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
