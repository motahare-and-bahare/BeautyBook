"""Shared test fixtures: a migrated PostgreSQL database, API clients, and fast hashing."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.infrastructure.database import create_database_engine, get_session
from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
# Child tables first, so the same cleanup works on SQLite, which has no TRUNCATE.
_CLEANUP_ORDER = ("owner_applications", "sessions", "user_roles", "users")


def _alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    # ``%`` is an interpolation character in .ini files.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def _build_api_client(engine: Engine) -> TestClient:
    app = create_app()
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def fast_password_hashing() -> Iterator[None]:
    """Keep Argon2id fast during tests while the defaults stay production-strength."""

    settings = get_settings()
    original = (
        settings.argon2_time_cost,
        settings.argon2_memory_cost,
        settings.argon2_parallelism,
    )
    settings.argon2_time_cost = 1
    settings.argon2_memory_cost = 8192
    settings.argon2_parallelism = 1
    try:
        yield
    finally:
        (
            settings.argon2_time_cost,
            settings.argon2_memory_cost,
            settings.argon2_parallelism,
        ) = original


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    settings = get_settings()
    test_url = settings.test_database_url

    if not test_url:
        pytest.skip("TEST_DATABASE_URL is required for integration tests.")
    if test_url == settings.database_url:
        pytest.fail("TEST_DATABASE_URL must point to a different database.")

    config = _alembic_config(test_url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_database_engine(test_url)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(config, "base")


@pytest.fixture()
def clean_database(test_engine: Engine) -> None:
    with test_engine.begin() as connection:
        for table in _CLEANUP_ORDER:
            connection.execute(text(f"DELETE FROM {table}"))


@pytest.fixture()
def db_session(test_engine: Engine, clean_database: None) -> Iterator[Session]:
    session = sessionmaker(bind=test_engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_client(test_engine: Engine, clean_database: None) -> Iterator[TestClient]:
    with _build_api_client(test_engine) as client:
        yield client


@pytest.fixture()
def api_client_factory(
    test_engine: Engine,
    clean_database: None,
) -> Iterator[Callable[[], TestClient]]:
    """Build one independent client per thread for concurrency tests."""

    clients: list[TestClient] = []

    def build() -> TestClient:
        client = _build_api_client(test_engine)
        clients.append(client)
        return client

    try:
        yield build
    finally:
        for client in clients:
            client.close()
