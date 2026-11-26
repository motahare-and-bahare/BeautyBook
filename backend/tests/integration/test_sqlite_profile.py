"""The SQLite profile: pragmas, foreign-key enforcement, and aware UTC datetimes.

These tests defend the four behaviours that differ from PostgreSQL. They are the reason the
switch is safe rather than optimistic.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.database import Base, build_engine
from app.modules.identity.models import AuthSession, User, UserRole

CSRF_PATH = "/api/v1/auth/csrf"
REGISTER_PATH = "/api/v1/auth/register/customer"
LOGIN_PATH = "/api/v1/auth/login"
ME_PATH = "/api/v1/auth/me"
PASSWORD = "correct horse battery staple"


@pytest.fixture()
def sqlite_engine(tmp_path: Path) -> Iterator[Engine]:
    engine = build_engine(f"sqlite:///{tmp_path / 'profile.db'}")
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def csrf_headers(client: TestClient) -> dict[str, str]:
    token = client.get(CSRF_PATH).json()["csrf_token"]
    return {get_settings().csrf_header_name: token}


def test_sqlite_pragmas_are_enabled(sqlite_engine: Engine) -> None:
    with sqlite_engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1
        assert connection.execute(text("PRAGMA busy_timeout")).scalar() > 0
        assert str(connection.execute(text("PRAGMA journal_mode")).scalar()).lower() == "wal"


def test_deleting_a_user_cascades_on_sqlite(sqlite_engine: Engine) -> None:
    factory = sessionmaker(bind=sqlite_engine, expire_on_commit=False)

    with factory() as session:
        user = User(full_name="Cascade Check", email="cascade@example.com", password_hash="x")
        session.add(user)
        session.flush()
        session.add(UserRole(user_id=user.id, role="customer"))
        session.add(
            AuthSession(
                user_id=user.id,
                token_hash="a" * 64,
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )
        session.commit()

        session.delete(user)
        session.commit()

        assert session.scalar(select(func.count()).select_from(User)) == 0
        assert session.scalar(select(func.count()).select_from(UserRole)) == 0
        assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_datetimes_round_trip_as_aware_utc(sqlite_engine: Engine) -> None:
    factory = sessionmaker(bind=sqlite_engine, expire_on_commit=False)
    original = datetime(2026, 11, 24, 9, 30, 15, 123456, tzinfo=UTC)

    with factory() as session:
        user = User(full_name="Time Check", email="time@example.com", password_hash="x")
        session.add(user)
        session.flush()
        session.add(AuthSession(user_id=user.id, token_hash="b" * 64, expires_at=original))
        session.commit()

    with factory() as session:
        stored = session.scalars(select(AuthSession)).one()

        assert stored.expires_at.tzinfo is not None
        assert stored.expires_at == original


def test_default_profile_is_sqlite(test_engine: Engine) -> None:
    if get_settings().test_database_url:
        pytest.skip("TEST_DATABASE_URL selects an explicit database profile.")

    assert test_engine.dialect.name == "sqlite"


def test_register_login_and_me_work_on_the_configured_profile(api_client: TestClient) -> None:
    email = "sqlite-profile@example.com"
    payload = {"full_name": "SQLite Profile", "email": email, "password": PASSWORD}

    registered = api_client.post(REGISTER_PATH, headers=csrf_headers(api_client), json=payload)
    assert registered.status_code == 201
    assert registered.json()["email"] == email

    duplicate = api_client.post(REGISTER_PATH, headers=csrf_headers(api_client), json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    signed_in = api_client.post(
        LOGIN_PATH,
        headers=csrf_headers(api_client),
        json={"email": email, "password": PASSWORD},
    )
    assert signed_in.status_code == 200

    me = api_client.get(ME_PATH)
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_ready_reports_the_database_is_available(api_client: TestClient) -> None:
    response = api_client.get("/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"
