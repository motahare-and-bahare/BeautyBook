"""The application factory must be importable without side effects."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI

from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_create_app_returns_a_fastapi_application() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    paths = set(app.openapi()["paths"])
    assert "/health" in paths
    assert "/ready" in paths


def test_importing_the_app_does_not_load_the_cli() -> None:
    """Checked in a fresh interpreter so another test's imports cannot mask the result."""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.main, sys; print('app.cli' in sys.modules)",
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "False"


def test_create_app_is_repeatable() -> None:
    assert create_app() is not create_app()
