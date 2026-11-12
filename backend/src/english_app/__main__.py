"""Run the app: `python -m english_app`."""

import logging

import uvicorn

from english_app.core.config import get_settings
from english_app.main import create_app


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    settings = get_settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
