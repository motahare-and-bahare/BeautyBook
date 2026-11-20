"""The domain module must stay free of web and database frameworks."""

from __future__ import annotations

from pathlib import Path

from app.modules.identity import domain


def test_domain_module_imports_no_web_or_database_framework() -> None:
    source = Path(domain.__file__).read_text(encoding="utf-8").lower()

    assert "fastapi" not in source
    assert "sqlalchemy" not in source
