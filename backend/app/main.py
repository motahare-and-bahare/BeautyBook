"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.errors import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging


def create_app() -> FastAPI:
    """Build the application.

    Importing this module must not open a database connection or read secrets beyond
    configuration validation.
    """

    configure_logging()

    app = FastAPI(
        title="BeautyBook API",
        version="0.1.0",
        description="Authentication and marketplace API for BeautyBook.",
    )
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
