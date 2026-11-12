"""Jinja2 prompt templates kept next to each module, separate from code."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class PromptRenderer:
    def __init__(self, directory: Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(directory),
            undefined=StrictUndefined,  # a missing variable is a bug, not an empty string
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,  # plain-text prompts, never rendered as HTML
        )

    def render(self, name: str, **context: Any) -> str:
        return self._env.get_template(name).render(**context).strip()
