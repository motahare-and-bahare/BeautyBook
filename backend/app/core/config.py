"""Application configuration loaded from environment variables.

Configuration is validated at startup so the application fails clearly when a required
value is missing or malformed. Secrets are never hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["development", "test", "production"]

POSTGRESQL_PREFIX = "postgresql+psycopg://"
SQLITE_PREFIXES = ("sqlite+pysqlite://", "sqlite://")


class Settings(BaseSettings):
    """Validated runtime settings.

    Values come from environment variables, then from the closest ``.env`` file, then from
    the defaults below. ``DATABASE_URL`` has no default on purpose: a missing database
    configuration must stop the application instead of silently using a local file.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = "development"
    database_url: str
    test_database_url: str | None = None

    session_ttl_days: int = Field(default=7, ge=1, le=30)
    session_cookie_secure: bool | None = None

    session_cookie_name: str = "beautybook_session"
    csrf_cookie_name: str = "beautybook_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    argon2_time_cost: int = Field(default=3, ge=1)
    argon2_memory_cost: int = Field(default=65536, ge=8192)
    argon2_parallelism: int = Field(default=4, ge=1)

    @field_validator("database_url", "test_database_url")
    @classmethod
    def require_supported_database_url(cls, value: str | None) -> str | None:
        """Accept the production PostgreSQL driver and the local SQLite driver only.

        PostgreSQL remains the production database. SQLite is accepted for a local,
        single-operator deployment and for tests (ADR-0011); it cannot provide the booking
        concurrency guarantees that PostgreSQL provides.
        """

        if value is None:
            return None
        if value.startswith(POSTGRESQL_PREFIX) or value.startswith(SQLITE_PREFIXES):
            return value
        raise ValueError(
            "must be a PostgreSQL URL using the psycopg driver "
            f"({POSTGRESQL_PREFIX}...) or a SQLite URL (sqlite+pysqlite:///...)"
        )

    @property
    def secure_cookies(self) -> bool:
        """Cookies are secure in production unless explicitly overridden."""

        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""

    # Environment variables and the .env file provide ``database_url`` at runtime.
    return Settings()  # type: ignore[call-arg]
