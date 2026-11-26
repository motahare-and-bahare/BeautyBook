"""Administrator user list: role gate, safe projection, and keyset pagination.

The endpoint is administrator-only. It must never answer a caller without the ``admin`` role,
must never expose a password hash or session token, and must page through accounts without
skipping or repeating a row.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.modules.identity.domain import Role, UserStatus
from app.modules.identity.models import User, UserRole
from app.modules.identity.service import create_session_for_user

USERS_PATH = "/api/v1/admin/users"
PASSWORD = "correct horse battery staple"
BASE_TIME = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)


def unique_email(label: str) -> str:
    return f"{label}-{uuid.uuid4().hex}@example.com"


def create_user(
    db_session: Session,
    *,
    email: str,
    roles: tuple[Role, ...] = (Role.CUSTOMER,),
    created_at: datetime | None = None,
) -> User:
    user = User(
        full_name="Listed User",
        email=email,
        password_hash=hash_password(PASSWORD),
        status=UserStatus.ACTIVE.value,
    )
    if created_at is not None:
        user.created_at = created_at
        user.updated_at = created_at
    db_session.add(user)
    db_session.flush()
    for role in roles:
        db_session.add(UserRole(user_id=user.id, role=role.value))
    db_session.commit()
    return user


def sign_in(api_client: TestClient, db_session: Session, user: User) -> None:
    _, raw_token = create_session_for_user(db_session, user)
    db_session.commit()
    api_client.cookies.set(get_settings().session_cookie_name, raw_token)


def create_admin(api_client: TestClient, db_session: Session) -> User:
    admin = create_user(
        db_session,
        email=unique_email("admin"),
        roles=(Role.ADMIN, Role.CUSTOMER),
        created_at=BASE_TIME,
    )
    sign_in(api_client, db_session, admin)
    return admin


def test_lists_accounts_newest_first_with_roles_and_no_secrets(
    api_client: TestClient,
    db_session: Session,
) -> None:
    admin = create_admin(api_client, db_session)
    older = create_user(
        db_session,
        email=unique_email("older"),
        roles=(Role.CUSTOMER,),
        created_at=BASE_TIME + timedelta(minutes=1),
    )
    newer = create_user(
        db_session,
        email=unique_email("newer"),
        roles=(Role.CUSTOMER, Role.SALON_OWNER),
        created_at=BASE_TIME + timedelta(minutes=2),
    )

    response = api_client.get(USERS_PATH)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [str(newer.id), str(older.id), str(admin.id)]
    assert body["next_cursor"] is None

    by_id = {item["id"]: item for item in body["items"]}
    assert by_id[str(admin.id)]["roles"] == ["admin", "customer"]
    assert by_id[str(newer.id)]["roles"] == ["customer", "salon_owner"]
    assert by_id[str(older.id)]["status"] == "active"
    assert set(by_id[str(older.id)]) == {
        "id",
        "full_name",
        "email",
        "roles",
        "status",
        "created_at",
    }

    assert PASSWORD not in response.text
    assert "password_hash" not in response.text
    assert newer.password_hash not in response.text


def test_pagination_returns_each_account_exactly_once(
    api_client: TestClient,
    db_session: Session,
) -> None:
    admin = create_admin(api_client, db_session)
    created = [
        create_user(
            db_session,
            email=unique_email(f"page-{index}"),
            created_at=BASE_TIME + timedelta(minutes=index + 1),
        )
        for index in range(2)
    ]

    first = api_client.get(USERS_PATH, params={"limit": 2})
    assert first.status_code == 200
    first_body = first.json()
    assert [item["id"] for item in first_body["items"]] == [str(created[1].id), str(created[0].id)]
    assert first_body["next_cursor"]

    second = api_client.get(USERS_PATH, params={"limit": 2, "cursor": first_body["next_cursor"]})
    assert second.status_code == 200
    second_body = second.json()
    assert [item["id"] for item in second_body["items"]] == [str(admin.id)]
    assert second_body["next_cursor"] is None

    all_ids = [item["id"] for item in first_body["items"] + second_body["items"]]
    assert len(all_ids) == len(set(all_ids)) == 3


def test_the_default_page_size_is_bounded(
    api_client: TestClient,
    db_session: Session,
) -> None:
    create_admin(api_client, db_session)
    for index in range(24):
        create_user(
            db_session,
            email=unique_email(f"many-{index}"),
            created_at=BASE_TIME + timedelta(seconds=index + 1),
        )

    response = api_client.get(USERS_PATH)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 20
    assert body["next_cursor"]


def test_a_single_account_has_no_next_cursor(
    api_client: TestClient,
    db_session: Session,
) -> None:
    create_admin(api_client, db_session)

    response = api_client.get(USERS_PATH, params={"limit": 1})
    body = response.json()

    assert response.status_code == 200
    assert len(body["items"]) == 1
    assert body["next_cursor"] is None


def test_a_non_admin_is_forbidden(
    api_client: TestClient,
    db_session: Session,
) -> None:
    customer = create_user(db_session, email=unique_email("customer"))
    sign_in(api_client, db_session, customer)

    response = api_client.get(USERS_PATH)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_a_salon_owner_is_forbidden(
    api_client: TestClient,
    db_session: Session,
) -> None:
    owner = create_user(
        db_session,
        email=unique_email("owner"),
        roles=(Role.CUSTOMER, Role.SALON_OWNER),
    )
    sign_in(api_client, db_session, owner)

    assert api_client.get(USERS_PATH).status_code == 403


def test_an_unauthenticated_request_is_401(api_client: TestClient) -> None:
    response = api_client.get(USERS_PATH)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_an_invalid_cursor_is_rejected(
    api_client: TestClient,
    db_session: Session,
) -> None:
    create_admin(api_client, db_session)

    response = api_client.get(USERS_PATH, params={"cursor": "not-a-real-cursor"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_CURSOR"
    assert "cursor" in error["fields"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}])
def test_a_page_size_outside_the_range_is_rejected(
    api_client: TestClient,
    db_session: Session,
    params: dict[str, int],
) -> None:
    create_admin(api_client, db_session)

    response = api_client.get(USERS_PATH, params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_a_role_granted_later_appears_on_the_next_request(
    api_client: TestClient,
    db_session: Session,
) -> None:
    create_admin(api_client, db_session)
    customer = create_user(db_session, email=unique_email("promoted"))

    before = api_client.get(USERS_PATH).json()
    roles_before = next(item for item in before["items"] if item["id"] == str(customer.id))["roles"]
    assert roles_before == ["customer"]

    db_session.add(UserRole(user_id=customer.id, role=Role.SALON_OWNER.value))
    db_session.commit()

    after = api_client.get(USERS_PATH).json()
    roles_after = next(item for item in after["items"] if item["id"] == str(customer.id))["roles"]
    assert roles_after == ["customer", "salon_owner"]
