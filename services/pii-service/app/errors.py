"""Errors raised while configuring the PII service."""

from collections.abc import Iterable


class PiiServiceError(Exception):
    """Base class for errors of the PII service."""


class UnknownBackendError(PiiServiceError):
    """The configured detector backend is not registered in the factory."""

    def __init__(self, name: str, available: Iterable[str]) -> None:
        super().__init__(
            f"Unknown PII backend '{name}'. Available backends: {', '.join(sorted(available))}"
        )


class BackendAlreadyRegisteredError(PiiServiceError):
    """A second builder was registered under an existing backend name."""

    def __init__(self, name: str) -> None:
        super().__init__(f"PII backend '{name}' is already registered")


class MissingDependencyError(PiiServiceError):
    """The backend needs optional packages that are not installed."""

    def __init__(self, backend: str, module: str) -> None:
        super().__init__(
            f"PII backend '{backend}' needs the optional package '{module}'. "
            "Install the model dependencies with: pip install '.[ml]'"
        )
