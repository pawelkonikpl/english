"""Domain errors and their mapping to HTTP responses.

Every error carries a stable `code` for clients and a `user_message` in Polish that the
UI can show as is. `str(error)` stays an English developer message for logs.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for errors that are reported to the client."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"
    default_user_message: str = "Coś poszło nie tak."

    def __init__(self, message: str, *, user_message: str | None = None) -> None:
        super().__init__(message)
        self.user_message = user_message or self.default_user_message


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    default_user_message = "Nie znaleziono."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    default_user_message = "Operacja jest w konflikcie z aktualnym stanem."


class InvalidInputError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "invalid_input"
    default_user_message = "Nieprawidłowe dane."


class ConfigurationError(Exception):
    """Invalid configuration detected at startup. Stops the application."""


def error_body(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.warning("%s %s failed: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.user_message))


async def _handle_request_validation(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'][1:]) or 'body'}: {error['msg']}"
        for error in exc.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_body(InvalidInputError.code, f"Nieprawidłowe dane ({details})."),
    )


async def _handle_http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        body = error_body(NotFoundError.code, "Nie znaleziono.")
    else:
        body = error_body("http_error", str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_request_validation)
    app.add_exception_handler(StarletteHTTPException, _handle_http_error)
