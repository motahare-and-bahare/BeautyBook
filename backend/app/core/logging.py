"""Request correlation and logging configuration.

Every request gets an id that appears in the response header and in log lines. Log records
must never contain passwords, session tokens, or personal data.
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_LOG_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"


def current_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    """Adds the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Configure one console handler without duplicating handlers on repeated calls."""

    root = logging.getLogger()
    root.setLevel(level)

    if any(getattr(handler, "_beautybook_handler", False) for handler in root.handlers):
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    handler.addFilter(RequestIdFilter())
    handler._beautybook_handler = True  # type: ignore[attr-defined]
    root.addHandler(handler)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns a request id, exposes it as a header, and logs the request outcome."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        token = _request_id.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "request_completed method=%s path=%s status=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
            )
            return response
        finally:
            _request_id.reset(token)
