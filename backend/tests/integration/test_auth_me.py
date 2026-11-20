"""Current-user endpoint: session resolution, roles, and failure paths.

``GET /api/v1/auth/me`` is the first protected endpoint. It must resolve the opaque cookie to a
database session on every request, read roles from the database (never from cached session data),
and reject every invalid session with the same ``401 UNAUTHENTICATED`` response.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.modules.identity.domain import Role, UserStatus
from app.modules.identity.models import User, UserRole
from app.modules.identity.service import create_session_for_user, revoke_session

ME_PATH = "/api/v1/auth/me"
PASSWORD = "correct horse battery staple"


def unique_email() -> str:
    return f"me-{uuid.uuid4().hex}@example.com"


def create_user(
    db_session: Session,
    *,
    roles: tuple[Role, ...] = (Role.CUSTOMER,),
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    user = User(
        full_name="Current User",
        email=unique_email(),
        password_hash=hash_password(PASSWORD),
        status=status.value,
    )
    db_session.add(user)
    db_session.flush()
    for role in roles:
        db_session.add(UserRole(user_id=user.id, role=role.value))
    db_session.commit()
    return user


def sign_in(
    api_client: TestClient,
    db_session: Session,
    user: User,
    *,
    now: datetime | None = None,
) -> str:
    auth_session, raw_token = create_session_for_user(db_session, user, now=now)
    db_session.commit()
    api_client.cookies.set(get_settings().session_cookie_name, raw_token)
    return raw_token


def test_me_returns_the_current_user_and_reads_roles_from_the_database(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)
    raw_token = sign_in(api_client, db_session, user)

    response = api_client.get(ME_PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["full_name"] == "Current User"
    assert body["email"] == user.email
    assert body["roles"] == ["customer"]
    assert body["status"] == "active"
    assert set(body) == {"id", "full_name", "email", "roles", "status", "created_at"}

    assert PASSWORD not in response.text
    assert user.password_hash not in response.text
    assert raw_token not in response.text

    # A role granted after the session was created must appear on the next request.
    db_session.add(UserRole(user_id=user.id, role=Role.SALON_OWNER.value))
    db_session.commit()

    refreshed = api_client.get(ME_PATH)

    assert refreshed.status_code == 200
    assert refreshed.json()["roles"] == ["customer", "salon_owner"]


def test_me_without_a_session_returns_401(
    api_client: TestClient,
) -> None:
    response = api_client.get(ME_PATH)

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHENTICATED"
    assert error["fields"] == {}
    assert error["request_id"]


def test_me_rejects_an_unknown_session_token(
    api_client: TestClient,
) -> None:
    api_client.cookies.set(get_settings().session_cookie_name, "not-a-real-session-token")

    response = api_client.get(ME_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_rejects_an_expired_session(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)
    sign_in(api_client, db_session, user, now=datetime.now(UTC) - timedelta(days=8))

    response = api_client.get(ME_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_rejects_a_revoked_session(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)
    auth_session, raw_token = create_session_for_user(db_session, user)
    db_session.commit()
    revoke_session(db_session, auth_session)
    db_session.commit()
    api_client.cookies.set(get_settings().session_cookie_name, raw_token)

    response = api_client.get(ME_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    "status",
    [UserStatus.PENDING_APPROVAL, UserStatus.REJECTED, UserStatus.SUSPENDED],
)
def test_me_rejects_a_user_who_is_no_longer_active(
    api_client: TestClient,
    db_session: Session,
    status: UserStatus,
) -> None:
    user = create_user(db_session)
    sign_in(api_client, db_session, user)

    user.status = status.value
    db_session.commit()

    response = api_client.get(ME_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_logs_never_contain_the_email_token_or_password(
    api_client: TestClient,
    db_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    user = create_user(db_session)
    raw_token = sign_in(api_client, db_session, user)

    response = api_client.get(ME_PATH)

    assert response.status_code == 200
    assert PASSWORD not in caplog.text
    assert user.email not in caplog.text
    assert raw_token not in caplog.text
