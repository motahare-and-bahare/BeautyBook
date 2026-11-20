"""Login and account-status handling against PostgreSQL.

The login flow is security-sensitive: an unknown email and a wrong password must be
indistinguishable, account status may be revealed only after a correct password, and only an
active account may receive a session. These tests assert database state as well as HTTP bodies.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping

import httpx
import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, hash_session_token, verify_password
from app.modules.identity import service
from app.modules.identity.domain import Role, UserStatus
from app.modules.identity.models import AuthSession, User, UserRole
from app.modules.identity.service import create_session_for_user

CSRF_PATH = "/api/v1/auth/csrf"
LOGIN_PATH = "/api/v1/auth/login"
PASSWORD = "correct horse battery staple"
WRONG_PASSWORD = "this is not the right password"


def unique_email() -> str:
    return f"login-{uuid.uuid4().hex}@example.com"


def csrf_headers(client: TestClient) -> dict[str, str]:
    response = client.get(CSRF_PATH)
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {get_settings().csrf_header_name: token}


def login(
    client: TestClient,
    email: str,
    password: str = PASSWORD,
    *,
    extra: Mapping[str, object] | None = None,
) -> httpx.Response:
    body: dict[str, object] = {"email": email, "password": password}
    if extra:
        body.update(extra)
    return client.post(LOGIN_PATH, headers=csrf_headers(client), json=body)


def create_user(
    db_session: Session,
    *,
    email: str | None = None,
    status: UserStatus = UserStatus.ACTIVE,
    password: str = PASSWORD,
    password_hash: str | None = None,
    with_customer_role: bool = True,
) -> User:
    user = User(
        full_name="Login User",
        email=email or unique_email(),
        password_hash=password_hash or hash_password(password),
        status=status.value,
    )
    db_session.add(user)
    db_session.flush()
    if with_customer_role:
        db_session.add(UserRole(user_id=user.id, role=Role.CUSTOMER.value))
    db_session.commit()
    return user


def count_sessions(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(AuthSession)) or 0


def cookie_header(response: httpx.Response, name: str) -> str:
    for header in response.headers.get_list("set-cookie"):
        if header.startswith(f"{name}="):
            return header
    raise AssertionError(f"cookie {name} was not set")


def cookie_value(response: httpx.Response, name: str) -> str:
    return cookie_header(response, name).split("=", 1)[1].split(";", 1)[0]


def test_active_login_returns_a_user_and_a_new_session(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)

    response = login(api_client, "  " + user.email.upper() + "  ")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == user.email
    assert body["full_name"] == "Login User"
    assert body["roles"] == ["customer"]
    assert body["status"] == "active"
    assert set(body) == {"id", "full_name", "email", "roles", "status", "created_at"}

    assert PASSWORD not in response.text
    assert user.password_hash not in response.text

    settings = get_settings()
    raw_token = api_client.cookies.get(settings.session_cookie_name)
    assert raw_token
    assert raw_token not in response.text

    session_cookie = cookie_header(response, settings.session_cookie_name)
    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie

    auth_session = db_session.scalar(select(AuthSession))
    assert auth_session is not None
    assert auth_session.user_id == user.id
    assert auth_session.revoked_at is None
    assert auth_session.token_hash == hash_session_token(raw_token)
    assert count_sessions(db_session) == 1


def test_a_wrong_password_and_an_unknown_email_are_indistinguishable(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)

    wrong_password = login(api_client, user.email, WRONG_PASSWORD)
    unknown_email = login(api_client, unique_email(), PASSWORD)

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert unknown_email.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]
    assert wrong_password.json()["error"]["fields"] == {}
    assert unknown_email.json()["error"]["fields"] == {}

    assert PASSWORD not in wrong_password.text
    assert PASSWORD not in unknown_email.text

    # No session may be created for a failed attempt.
    assert count_sessions(db_session) == 0


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (UserStatus.PENDING_APPROVAL, "ACCOUNT_PENDING_APPROVAL"),
        (UserStatus.REJECTED, "ACCOUNT_REJECTED"),
        (UserStatus.SUSPENDED, "ACCOUNT_SUSPENDED"),
    ],
)
def test_account_status_is_revealed_only_after_a_correct_password(
    api_client: TestClient,
    db_session: Session,
    status: UserStatus,
    code: str,
) -> None:
    user = create_user(db_session, status=status)

    wrong_password = login(api_client, user.email, WRONG_PASSWORD)
    assert wrong_password.status_code == 401
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"

    blocked = login(api_client, user.email, PASSWORD)
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == code
    assert blocked.json()["error"]["request_id"]
    assert db_session.scalar(select(func.count()).select_from(AuthSession)) == 0

    settings = get_settings()
    assert api_client.cookies.get(settings.session_cookie_name) is None


def test_login_normalizes_the_email_before_lookup(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session, email=unique_email())

    response = login(api_client, "  " + user.email.upper() + "  ")

    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)


def test_login_rotates_the_current_session_and_keeps_other_sessions(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)
    current, current_token = create_session_for_user(db_session, user)
    _, other_token = create_session_for_user(db_session, user)
    db_session.commit()

    settings = get_settings()
    api_client.cookies.set(settings.session_cookie_name, current_token)

    response = login(api_client, user.email)

    assert response.status_code == 200
    new_token = cookie_value(response, settings.session_cookie_name)
    assert new_token
    assert new_token != current_token

    db_session.expire_all()
    rotated = db_session.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(current_token))
    )
    untouched = db_session.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(other_token))
    )
    replacement = db_session.scalar(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(new_token))
    )

    assert rotated is not None
    assert rotated.revoked_at is not None
    assert untouched is not None
    assert untouched.revoked_at is None
    assert replacement is not None
    assert replacement.revoked_at is None
    assert count_sessions(db_session) == 3


def test_login_verifies_an_argon2id_hash(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)
    assert user.password_hash.startswith("$argon2id$")

    response = login(api_client, user.email, PASSWORD)

    assert response.status_code == 200
    assert verify_password(PASSWORD, user.password_hash)


def test_login_rehashes_an_outdated_stored_hash(
    api_client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    weak_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    user = create_user(db_session, password_hash=weak_hash)

    settings = get_settings()
    monkeypatch.setattr(settings, "argon2_time_cost", 2)

    response = login(api_client, user.email, PASSWORD)

    assert response.status_code == 200
    db_session.expire_all()
    refreshed = db_session.get(User, user.id)
    assert refreshed is not None
    assert refreshed.password_hash != weak_hash
    assert "t=2" in refreshed.password_hash
    assert verify_password(PASSWORD, refreshed.password_hash)


def test_an_unknown_email_still_runs_a_dummy_password_verification(
    db_session: Session,
) -> None:
    checked_hashes: list[str] = []

    def verifier(password: str, password_hash: str) -> bool:
        checked_hashes.append(password_hash)
        return False

    with pytest.raises(service.InvalidCredentialsError):
        service.login(
            db_session,
            email=unique_email(),
            password=PASSWORD,
            password_verifier=verifier,
        )

    assert len(checked_hashes) == 1
    assert checked_hashes[0].startswith("$argon2id$")


def test_missing_csrf_token_is_rejected_before_any_database_write(
    api_client: TestClient,
    db_session: Session,
) -> None:
    user = create_user(db_session)

    response = api_client.post(LOGIN_PATH, json={"email": user.email, "password": PASSWORD})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"
    assert count_sessions(db_session) == 0


@pytest.mark.parametrize(
    "invalid",
    [
        {"email": "not-an-email"},
        {"email": ""},
        {"password": ""},
        {"password": "a" * 129},
    ],
)
def test_malformed_login_input_returns_422_without_a_session(
    api_client: TestClient,
    db_session: Session,
    invalid: dict[str, object],
) -> None:
    user = create_user(db_session)
    body: dict[str, object] = {"email": user.email, "password": PASSWORD}
    body.update(invalid)

    response = api_client.post(LOGIN_PATH, headers=csrf_headers(api_client), json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Value error" not in response.text
    assert count_sessions(db_session) == 0


@pytest.mark.parametrize(
    "privileged_field",
    [
        {"role": "admin"},
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
    user = create_user(db_session)

    response = login(api_client, user.email, extra=privileged_field)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert next(iter(privileged_field)) in response.json()["error"]["fields"]
    assert count_sessions(db_session) == 0


def test_login_logs_never_contain_the_email_or_password(
    api_client: TestClient,
    db_session: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    user = create_user(db_session)

    success = login(api_client, user.email)
    failure = login(api_client, user.email, WRONG_PASSWORD)

    assert success.status_code == 200
    assert failure.status_code == 401
    assert PASSWORD not in caplog.text
    assert WRONG_PASSWORD not in caplog.text
    assert user.email not in caplog.text
    assert "login_success" in caplog.text
    assert "login_failure" in caplog.text
