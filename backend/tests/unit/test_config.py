"""Configuration must fail clearly and provide safe defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings

VALID_URL = "postgresql+psycopg://user:secret@127.0.0.1:5432/beautybook"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


def test_non_postgresql_database_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match=r"postgresql\+psycopg"):
        make_settings(database_url="sqlite:///beautybook.db")


def test_invalid_app_env_is_rejected() -> None:
    with pytest.raises(ValidationError, match="app_env"):
        make_settings(app_env="staging")


def test_safe_defaults() -> None:
    settings = make_settings()

    assert settings.app_env == "development"
    assert settings.session_ttl_days == 7
    assert settings.secure_cookies is False
    assert settings.session_cookie_name == "beautybook_session"
    assert settings.csrf_cookie_name == "beautybook_csrf"
    assert settings.csrf_header_name == "X-CSRF-Token"
    assert settings.argon2_time_cost == 3
    assert settings.argon2_memory_cost == 65536
    assert settings.argon2_parallelism == 4


def test_production_enables_secure_cookies() -> None:
    assert make_settings(app_env="production").secure_cookies is True


def test_explicit_cookie_setting_wins_over_environment_default() -> None:
    settings = make_settings(app_env="production", session_cookie_secure=False)

    assert settings.secure_cookies is False


@pytest.mark.parametrize("ttl", [0, 31])
def test_session_ttl_is_bounded(ttl: int) -> None:
    with pytest.raises(ValidationError, match="session_ttl_days"):
        make_settings(session_ttl_days=ttl)


def test_test_database_url_is_optional_but_validated() -> None:
    assert make_settings().test_database_url is None

    with pytest.raises(ValidationError, match=r"postgresql\+psycopg"):
        make_settings(test_database_url="mysql://not-supported")
