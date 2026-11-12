"""Service configuration, read from ``PII_*`` environment variables or a ``.env`` file."""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BACKEND = "bardsai-eu-pii"


class Settings(BaseSettings):
    """Runtime settings of the PII service."""

    model_config = SettingsConfigDict(
        env_prefix="PII_",
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    backend: str = Field(
        default=DEFAULT_BACKEND,
        description="Name of the detector backend registered in the detector factory.",
    )
    model_id: str | None = Field(
        default=None,
        description="Hugging Face model id that replaces the backend's default model.",
    )
    model_revision: str | None = Field(
        default=None,
        description="Model revision (branch, tag or commit) to pin the downloaded weights.",
    )
    device: str = Field(default="cpu", description="Torch device, e.g. 'cpu' or 'cuda'.")
    min_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Default confidence threshold; requests can override it.",
    )
    window_tokens: int = Field(
        default=512,
        ge=32,
        description="Tokens per model window; longer texts are split into overlapping windows.",
    )
    window_stride: int = Field(
        default=128,
        ge=0,
        description="Tokens shared by neighbouring windows.",
    )
    batch_size: int = Field(default=8, ge=1, description="Windows per forward pass.")

    @model_validator(mode="after")
    def check_window_stride(self) -> Self:
        # The tokenizer cannot move forward when the overlap fills half the window or more.
        if self.window_stride * 2 >= self.window_tokens:
            raise ValueError(
                f"window_stride ({self.window_stride}) must be less than half of "
                f"window_tokens ({self.window_tokens})"
            )
        return self
