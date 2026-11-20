"""Customer registration: atomic account creation, hashing, cookies, and safety.

Integration tests run against PostgreSQL. They assert database state, not only HTTP status
codes, because the guarantee is that user, role, and session are created together or not at all.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_session_token
from app.modules.identity import service
from app.modules.identity.models import AuthSession, User, UserRole

CSRF_PATH = "/api/v1/auth/csrf"
REGISTER_PATH = "/api/v1/auth/register/customer"
PASSWORD = "correct horse battery staple"

VALID_PAYLOAD: dict[str, object] = {
    "full_name": "Sara Ahmadi",
    "email": "sara@example.com",
    "password": PASSWORD,
}


def unique_email() -> str:
    return f"customer-{uuid.uuid4().hex}@example.com"


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get(CSRF_PATH)
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {get_settings().csrf_header_name: token}


def register(client: TestClient, payload: Mapping[str, object] | None = None) -> httpx.Response:
    body = dict(VALID_PAYLOAD)
    if payload:
        body.update(payload)
    return client.post(REGISTER_PATH, headers=csrf_headers(client), json=body)


def count(session: Session, model: type[User] | type[UserRole] | type[AuthSession]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def cookie_header(response: httpx.Response, name: str) -> str:
    headers = response.headers.get_list("set-cookie")
    for header in headers:
        if header.startswith(f"{name}="):
            return header
    raise AssertionError(f"cookie {name} was not set: {headers}")


def test_registration_creates_an_active_customer_with_a_session(
    api_client: TestClient,
    db_session: Session,
) -> None:
    payload = {
        "full_name": "  Sara Ahmadi  ",
        "email": "  Sara@Example.COM  ",
        "password": PASSWORD,
    }

    response = register(api_client, payload)

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Sara Ahmadi"
    assert body["email"] == "sara@example.com"
    assert body["roles"] == ["customer"]
    assert body["status"] == "active"
    assert body["id"]
    assert body["created_at"]

    # The response is a safe summary: no hash, no session token, no password.
    assert set(body) == {"id", "full_name", "email", "roles", "status", "created_at"}
    assert "password" not in response.text
    assert PASSWORD not in response.text

    settings = get_settings()
    raw_session_token = api_client.cookies.get(settings.session_cookie_name)
    assert raw_session_token
    assert raw_session_token not in response.text

    user = db_session.scalar(select(User))
    assert user is not None
    assert user.email == "sara@example.com"
    assert user.full_name == "Sara Ahmadi"
    assert user.status == "active"
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash

    role = db_session.scalar(select(UserRole))
    assert role is not None
    assert role.user_id == user.id
    assert role.role == "customer"
    assert count(db_session, UserRole) == 1

    auth_session = db_session.scalar(select(AuthSession))
    assert auth_session is not None
    assert auth_session.user_id == user.id
    assert auth_session.revoked_at is None
    assert auth_session.token_hash == hash_session_token(raw_session_token)
    assert auth_session.token_hash != raw_session_token
    assert count(db_session, AuthSession) == 1
    assert count(db_session, User) == 1


def test_session_cookie_is_httponly_and_csrf_cookie_is_readable(
    api_client: TestClient,
) -> None:
    settings = get_settings()

    response = register(api_client)
    assert response.status_code == 201

    session_cookie = cookie_header(response, settings.session_cookie_name)
    csrf_cookie = cookie_header(response, settings.csrf_cookie_name)

    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie
    assert "Path=/" in session_cookie
    assert "Max-Age=" in session_cookie
    assert "httponly" not in csrf_cookie.lower()
    assert "SameSite=lax" in csrf_cookie
    assert "Path=/" in csrf_cookie


def test_a_duplicate_email_is_rejected_case_insensitively(
    api_client: TestClient,
    db_session: Session,
) -> None:
    first = register(api_client)
    assert first.status_code == 201

    second = register(api_client, {"email": "SARA@EXAMPLE.COM"})

    assert second.status_code == 409
    error = second.json()["error"]
    assert error["code"] == "EMAIL_ALREADY_REGISTERED"
    assert error["request_id"]
    assert count(db_session, User) == 1
    assert count(db_session, UserRole) == 1
    assert count(db_session, AuthSession) == 1


@pytest.mark.parametrize(
    "invalid",
    [
        {"password": "a" * 11},
        {"password": "a" * 129},
        {"password": "            "},
        {"email": "not-an-email"},
        {"email": "@example.com"},
        {"email": "sara@example"},
        {"full_name": "A"},
        {"full_name": "   "},
        {"full_name": "Sara\x00Ahmadi"},
    ],
)
def test_invalid_input_returns_422_and_creates_nothing(
    api_client: TestClient,
    db_session: Session,
    invalid: dict[str, object],
) -> None:
    response = register(api_client, invalid)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["fields"]
    assert "Value error" not in response.text
    assert count(db_session, User) == 0
    assert count(db_session, UserRole) == 0
    assert count(db_session, AuthSession) == 0


@pytest.mark.parametrize(
    "privileged_field",
    [
        {"role": "admin"},
        {"role": "customer"},
        {"status": "active"},
        {"id": "8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60"},
        {"is_active": True},
    ],
)
def test_privileged_or_unknown_fields_are_rejected(
    api_client: TestClient,
    db_session: Session,
    privileged_field: dict[str, object],
) -> None:
    response = register(api_client, privileged_field)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    field_name = next(iter(privileged_field))
    assert field_name in response.json()["error"]["fields"]
    assert count(db_session, User) == 0


def test_missing_csrf_token_is_rejected_before_any_write(
    api_client: TestClient,
    db_session: Session,
) -> None:
    response = api_client.post(REGISTER_PATH, json=VALID_PAYLOAD)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"
    assert count(db_session, User) == 0
    assert count(db_session, UserRole) == 0
    assert count(db_session, AuthSession) == 0


@pytest.mark.parametrize("failing_step", ["role-assignment", "session-creation"])
def test_a_failure_midway_rolls_everything_back(
    api_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    failing_step: str,
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError(f"{failing_step} failed")

    if failing_step == "role-assignment":
        monkeypatch.setattr(service.repository, "add_role", fail)
    else:
        monkeypatch.setattr(service, "create_session_for_user", fail)

    with pytest.raises(RuntimeError):
        api_client.post(
            REGISTER_PATH,
            headers=csrf_headers(api_client),
            json=VALID_PAYLOAD,
        )

    db_session.expire_all()
    assert count(db_session, User) == 0
    assert count(db_session, UserRole) == 0
    assert count(db_session, AuthSession) == 0


def test_registration_logs_never_contain_the_email_or_password(
    api_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)

    response = register(api_client)

    assert response.status_code == 201
    assert PASSWORD not in caplog.text
    assert "sara@example.com" not in caplog.text
