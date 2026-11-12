"""Factory that builds the configured PII detector.

Backends are registered by name; ``Settings.backend`` picks one at startup. To add
a backend, write a class that satisfies ``PiiDetector`` and register a builder for
it in ``create_default_factory``. Nothing else in the service changes.
"""

from collections.abc import Callable, Mapping

from app.config import Settings
from app.detectors.base import PiiCategory, PiiDetector
from app.detectors.label_maps import BARDSAI_EU_PII_LABELS, OPENAI_PRIVACY_FILTER_LABELS
from app.detectors.regex_detector import RegexPiiDetector
from app.errors import BackendAlreadyRegisteredError, MissingDependencyError, UnknownBackendError

REGEX_BACKEND = "regex"
BARDSAI_EU_PII_BACKEND = "bardsai-eu-pii"
OPENAI_PRIVACY_FILTER_BACKEND = "openai-privacy-filter"

BARDSAI_EU_PII_MODEL_ID = "bardsai/eu-pii-anonimization-multilang-v3"
OPENAI_PRIVACY_FILTER_MODEL_ID = "openai/privacy-filter"

_ML_MODULES = frozenset({"torch", "transformers"})

DetectorBuilder = Callable[[Settings], PiiDetector]


class DetectorFactory:
    """Registry of detector builders, keyed by backend name."""

    def __init__(self) -> None:
        self._builders: dict[str, DetectorBuilder] = {}

    @property
    def backends(self) -> list[str]:
        return sorted(self._builders)

    def register(self, name: str, builder: DetectorBuilder) -> None:
        if name in self._builders:
            raise BackendAlreadyRegisteredError(name)
        self._builders[name] = builder

    def create(self, name: str, settings: Settings) -> PiiDetector:
        builder = self._builders.get(name)
        if builder is None:
            raise UnknownBackendError(name, self._builders)
        return builder(settings)


def create_default_factory() -> DetectorFactory:
    """Return a factory with every backend shipped with the service."""
    factory = DetectorFactory()
    factory.register(REGEX_BACKEND, _build_regex_detector)
    factory.register(
        BARDSAI_EU_PII_BACKEND,
        _transformers_builder(
            BARDSAI_EU_PII_BACKEND, BARDSAI_EU_PII_MODEL_ID, BARDSAI_EU_PII_LABELS
        ),
    )
    factory.register(
        OPENAI_PRIVACY_FILTER_BACKEND,
        _transformers_builder(
            OPENAI_PRIVACY_FILTER_BACKEND,
            OPENAI_PRIVACY_FILTER_MODEL_ID,
            OPENAI_PRIVACY_FILTER_LABELS,
        ),
    )
    return factory


def _build_regex_detector(settings: Settings) -> PiiDetector:
    return RegexPiiDetector()


def _transformers_builder(
    backend: str, default_model_id: str, label_map: Mapping[str, PiiCategory]
) -> DetectorBuilder:
    def build(settings: Settings) -> PiiDetector:
        try:
            # Imported here so that torch and transformers stay optional.
            from app.detectors.transformers_detector import TransformersPiiDetector
        except ModuleNotFoundError as exc:
            missing_module = (exc.name or "").partition(".")[0]
            if missing_module in _ML_MODULES:
                raise MissingDependencyError(backend, missing_module) from exc
            raise

        return TransformersPiiDetector(
            model_id=settings.model_id or default_model_id,
            label_map=label_map,
            revision=settings.model_revision,
            device=settings.device,
            window_tokens=settings.window_tokens,
            window_stride=settings.window_stride,
            batch_size=settings.batch_size,
        )

    return build
