"""The administrative CLI must stay outside the HTTP surface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_cli_is_not_mounted_as_an_http_route() -> None:
    paths = set(create_app().openapi()["paths"])

    assert [path for path in paths if "cli" in path.lower()] == []


def test_cli_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "--help"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "BeautyBook" in result.stdout
