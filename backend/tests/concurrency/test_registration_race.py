"""Concurrent customer registration: authoritative only on PostgreSQL.

The unique email constraint is the final protection. Two simultaneous requests for the same
address must produce exactly one account and one session; the loser receives a clean 409.

SQLite has a single writer and no row-level locking, so passing here would not prove the
production behaviour. ADR-0011 keeps this test PostgreSQL-only; the default SQLite profile
skips it with an explicit reason rather than reporting a false guarantee.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.identity.models import AuthSession, User, UserRole

CSRF_PATH = "/api/v1/auth/csrf"
REGISTER_PATH = "/api/v1/auth/register/customer"
PAYLOAD = {
    "full_name": "Race Condition",
    "email": "race@example.com",
    "password": "correct horse battery staple",
}


def submit(client: TestClient) -> httpx.Response:
    token = client.get(CSRF_PATH).json()["csrf_token"]
    return client.post(
        REGISTER_PATH,
        headers={get_settings().csrf_header_name: token},
        json=PAYLOAD,
    )


def count(session: Session, model: type[User] | type[UserRole] | type[AuthSession]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_two_simultaneous_registrations_create_exactly_one_account(
    api_client_factory: Callable[[], TestClient],
    db_session: Session,
    test_engine: Engine,
) -> None:
    if test_engine.dialect.name != "postgresql":
        pytest.skip(
            "Concurrency evidence requires PostgreSQL (ADR-0011). "
            "Set TEST_DATABASE_URL to a PostgreSQL URL to run this test."
        )

    clients = [api_client_factory(), api_client_factory()]

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, clients))

    statuses = sorted(response.status_code for response in responses)
    assert statuses == [201, 409]

    conflict = next(response for response in responses if response.status_code == 409)
    assert conflict.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

    assert count(db_session, User) == 1
    assert count(db_session, UserRole) == 1
    assert count(db_session, AuthSession) == 1
