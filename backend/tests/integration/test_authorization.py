"""Role-gated routes: ``require_roles`` must deny by default and allow a present role.

The dependency is exercised through real HTTP routes, not only as a plain function, because the
contract is the status code and error envelope that every future protected endpoint inherits.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.infrastructure.database import get_session
from app.main import create_app
from app.modules.identity.dependencies import require_roles
from app.modules.identity.domain import Role
from app.modules.identity.models import User, UserRole
from app.modules.identity.service import create_session_for_user

PROTECTED_PATH = "/__test__/role-protected"
PASSWORD = "correct horse battery staple"


def unique_email() -> str:
    return f"roles-{uuid.uuid4().hex}@example.com"


def create_user(db_session: Session, roles: tuple[Role, ...]) -> User:
    user = User(
        full_name="Role User",
        email=unique_email(),
        password_hash=hash_password(PASSWORD),
        status="active",
    )
    db_session.add(user)
    db_session.flush()
    for role in roles:
        db_session.add(UserRole(user_id=user.id, role=role.value))
    db_session.commit()
    return user


def sign_in(db_session: Session, user: User) -> str:
    _, raw_token = create_session_for_user(db_session, user)
    db_session.commit()
    return raw_token


def build_client(
    engine: Engine,
    dependency: Callable[..., Any],
    calls: list[str],
) -> TestClient:
    app = create_app()

    @app.get(PROTECTED_PATH, dependencies=[Depends(dependency)])
    def protected_route() -> dict[str, str]:
        calls.append("called")
        return {"status": "accepted"}

    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)


def test_a_missing_role_returns_403_and_never_calls_the_handler(
    test_engine: Engine,
    db_session: Session,
) -> None:
    calls: list[str] = []
    user = create_user(db_session, (Role.CUSTOMER,))
    raw_token = sign_in(db_session, user)

    with build_client(test_engine, require_roles(Role.ADMIN), calls) as client:
        client.cookies.set(get_settings().session_cookie_name, raw_token)
        response = client.get(PROTECTED_PATH)

    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "FORBIDDEN"
    assert error["fields"] == {}
    assert error["request_id"]
    assert calls == []


def test_a_present_role_is_allowed(
    test_engine: Engine,
    db_session: Session,
) -> None:
    calls: list[str] = []
    user = create_user(db_session, (Role.CUSTOMER, Role.ADMIN))
    raw_token = sign_in(db_session, user)

    with build_client(test_engine, require_roles(Role.ADMIN), calls) as client:
        client.cookies.set(get_settings().session_cookie_name, raw_token)
        response = client.get(PROTECTED_PATH)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    assert calls == ["called"]


def test_any_one_of_the_required_roles_is_enough(
    test_engine: Engine,
    db_session: Session,
) -> None:
    calls: list[str] = []
    user = create_user(db_session, (Role.CUSTOMER, Role.SALON_OWNER))
    raw_token = sign_in(db_session, user)

    with build_client(
        test_engine,
        require_roles(Role.ADMIN, Role.SALON_OWNER),
        calls,
    ) as client:
        client.cookies.set(get_settings().session_cookie_name, raw_token)
        response = client.get(PROTECTED_PATH)

    assert response.status_code == 200
    assert calls == ["called"]


def test_an_unauthenticated_request_is_401_not_403(
    test_engine: Engine,
    db_session: Session,
) -> None:
    calls: list[str] = []

    with build_client(test_engine, require_roles(Role.ADMIN), calls) as client:
        response = client.get(PROTECTED_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert calls == []


def test_a_role_change_takes_effect_on_the_next_request(
    test_engine: Engine,
    db_session: Session,
) -> None:
    calls: list[str] = []
    user = create_user(db_session, (Role.CUSTOMER,))
    raw_token = sign_in(db_session, user)

    with build_client(test_engine, require_roles(Role.ADMIN), calls) as client:
        client.cookies.set(get_settings().session_cookie_name, raw_token)
        denied = client.get(PROTECTED_PATH)

        db_session.add(UserRole(user_id=user.id, role=Role.ADMIN.value))
        db_session.commit()

        allowed = client.get(PROTECTED_PATH)

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert calls == ["called"]


@pytest.mark.parametrize("invalid", ["", "superuser"])
def test_an_unknown_required_role_is_rejected_at_wiring_time(invalid: str) -> None:
    with pytest.raises(ValueError):
        require_roles(invalid)
