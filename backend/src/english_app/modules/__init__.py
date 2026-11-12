"""Registry of feature modules available to the application.

Each module lives in its own package and exposes an `AppModule` instance as `module`.
"""

from english_app.core.modules import AppModule
from english_app.modules.phrases.module import module as phrases
from english_app.modules.profile.module import module as profile
from english_app.modules.progress.module import module as progress
from english_app.modules.review.module import module as review

AVAILABLE_MODULES: list[AppModule] = [profile, review, phrases, progress]
