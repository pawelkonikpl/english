"""Registry of feature modules available to the application.

Each module lives in its own package and exposes an `AppModule` instance as `module`.
"""

from english_app.core.modules import AppModule

AVAILABLE_MODULES: list[AppModule] = []
