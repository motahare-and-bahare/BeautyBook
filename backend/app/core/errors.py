"""One consistent error envelope for every API response."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

INTERNAL_ERROR_CODE = "INTERNAL_ERROR"
VALIDATION_ERROR_CODE = "VALIDATION_ERROR"


class AppError(Exception):
    """A failure that is safe to expose to the client with a stable code."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields or {}


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


def _error_body(
    request: Request,
    code: str,
    message: str,
    fields: dict[str, str] | None = None,
) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
            "fields": fields or {},
            "request_id": _request_id(request),
        }
    }


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppError):  # defensive: the handler is registered for AppError
        return await _handle_unexpected_error(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(request, exc.code, exc.message, exc.fields),
    )


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await _handle_unexpected_error(request, exc)

    fields: dict[str, str] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"] if part != "body") or "body"
        message = str(error["msg"]).removeprefix("Value error, ")
        fields[location] = message

    return JSONResponse(
        status_code=422,
        content=_error_body(
            request,
            VALIDATION_ERROR_CODE,
            "The request contains invalid values.",
            fields,
        ),
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error method=%s path=%s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(
            request,
            INTERNAL_ERROR_CODE,
            "An unexpected error occurred.",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)
