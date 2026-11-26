"""The admin user directory: admin-only, paginated, and secret-free."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.domain import Role
from app.modules.identity.models import User

USERS = "/api/v1/admin/users"


@pytest.fixture()
def admin_client(
    api_client: TestClient,
    create_account: Callable[..., User],
    sign_in_as: Callable[[TestClient, User], None],
) -> tuple[TestClient, User]:
    admin = create_account((Role.ADMIN,), full_name="Admin One")
    sign_in_as(api_client, admin)
    return api_client, admin


def test_admin_sees_users_with_their_roles(
    admin_client: tuple[TestClient, User],
    create_account: Callable[..., User],
) -> None:
    client, admin = admin_client
    customer = create_account((Role.CUSTOMER,), full_name="Customer One")
    owner = create_account((Role.SALON_OWNER,), full_name="Owner One")

    response = client.get(USERS)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    by_email = {item["email"]: item for item in body["items"]}
    assert by_email[admin.email]["roles"] == ["admin"]
    assert by_email[customer.email]["roles"] == ["customer"]
    assert by_email[owner.email]["roles"] == ["salon_owner"]


def test_the_directory_never_returns_secrets(
    admin_client: tuple[TestClient, User],
) -> None:
    client, _ = admin_client

    raw = client.get(USERS).text

    for forbidden in ("password_hash", "argon2", "token", "session"):
        assert forbidden not in raw.lower()


def test_pagination_returns_one_page_with_a_total(
    admin_client: tuple[TestClient, User],
    create_account: Callable[..., User],
) -> None:
    client, _ = admin_client
    for index in range(3):
        create_account((Role.CUSTOMER,), full_name=f"Person {index}")

    first = client.get(USERS, params={"limit": 2, "offset": 0})
    second = client.get(USERS, params={"limit": 2, "offset": 2})

    assert first.status_code == second.status_code == 200
    page = first.json()
    assert page["limit"] == 2
    assert page["offset"] == 0
    assert len(page["items"]) == 2
    assert page["total"] >= 4
    assert second.json()["offset"] == 2
    first_ids = {item["id"] for item in page["items"]}
    second_ids = {item["id"] for item in second.json()["items"]}
    assert first_ids.isdisjoint(second_ids)


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "many"}],
)
def test_invalid_pagination_is_rejected(
    admin_client: tuple[TestClient, User],
    params: dict[str, object],
) -> None:
    client, _ = admin_client

    response = client.get(USERS, params=params)

    assert response.status_code == 422


def test_a_guest_is_unauthenticated(api_client: TestClient) -> None:
    response = api_client.get(USERS)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("role", [Role.CUSTOMER, Role.SALON_OWNER])
def test_non_admin_roles_are_forbidden(
    api_client: TestClient,
    create_account: Callable[..., User],
    sign_in_as: Callable[[TestClient, User], None],
    role: Role,
) -> None:
    sign_in_as(api_client, create_account((role,)))

    response = api_client.get(USERS)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
