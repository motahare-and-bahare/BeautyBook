"""The application factory must be importable without side effects."""

from __future__ import annotations

import sys

from fastapi import FastAPI

from app.main import create_app


def test_create_app_returns_a_fastapi_application() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/ready" in paths


def test_importing_the_app_does_not_load_the_cli() -> None:
    assert "app.cli" not in sys.modules


def test_create_app_is_repeatable() -> None:
    assert create_app() is not create_app()
