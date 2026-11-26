"""Category taxonomy over real HTTP: public read, admin CRUD, and the role boundary."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.domain import Role
from app.modules.identity.models import User

PUBLIC = "/api/v1/categories"
ADMIN = "/api/v1/admin/categories"


def unique_slug(prefix: str = "cat") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def create_category(
    client: TestClient,
    headers: dict[str, str],
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": f"دسته {uuid.uuid4().hex[:6]}",
        "slug": unique_slug(),
        "description": "توضیح",
        "is_active": True,
        "sort_order": 0,
    }
    payload.update(overrides)
    return client.post(ADMIN, json=payload, headers=headers)


@pytest.fixture()
def admin_client(
    api_client: TestClient,
    create_account: Callable[..., User],
    sign_in_as: Callable[[TestClient, User], None],
    csrf_headers: dict[str, str],
) -> tuple[TestClient, dict[str, str]]:
    sign_in_as(api_client, create_account((Role.ADMIN,)))
    return api_client, csrf_headers


def test_public_list_needs_no_session_and_hides_inactive(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    active = create_category(client, headers, name="کوتاهی مو", is_active=True)
    create_category(client, headers, name="آرشیو شده", is_active=False)
    assert active.status_code == 201

    client.cookies.clear()
    response = client.get(PUBLIC)

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert "کوتاهی مو" in names
    assert "آرشیو شده" not in names


def test_public_list_is_ordered_by_sort_order(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    create_category(client, headers, name="سوم", slug=unique_slug("c"), sort_order=3)
    create_category(client, headers, name="اول", slug=unique_slug("a"), sort_order=1)
    create_category(client, headers, name="دوم", slug=unique_slug("b"), sort_order=2)

    client.cookies.clear()
    response = client.get(PUBLIC)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["اول", "دوم", "سوم"]


def test_create_returns_the_created_row(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    slug = unique_slug()

    response = create_category(client, headers, name="رنگ مو", slug=slug, sort_order=3)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "رنگ مو"
    assert body["slug"] == slug
    assert body["is_active"] is True
    assert body["sort_order"] == 3
    assert body["id"]
    assert body["created_at"] and body["updated_at"]
    # Internal uniqueness key must never leak.
    assert "name_key" not in body


def test_duplicate_slug_is_a_conflict(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    slug = unique_slug()
    assert create_category(client, headers, slug=slug).status_code == 201

    response = create_category(client, headers, name="نام دیگر", slug=slug)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_SLUG_TAKEN"


def test_duplicate_name_is_a_conflict_regardless_of_case(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    assert create_category(client, headers, name="Hair", slug=unique_slug()).status_code == 201

    response = create_category(client, headers, name="  hair ", slug=unique_slug())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_NAME_TAKEN"


@pytest.mark.parametrize("slug", ["Hair Cut", "-hair", "hair--cut", "کوتاهی"])
def test_invalid_slug_is_a_validation_error(
    admin_client: tuple[TestClient, dict[str, str]],
    slug: str,
) -> None:
    client, headers = admin_client

    response = create_category(client, headers, slug=slug)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "slug" in error["fields"]


def test_blank_name_is_a_validation_error(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client

    response = create_category(client, headers, name="   ")

    assert response.status_code == 422
    assert "name" in response.json()["error"]["fields"]


def test_unknown_category_id_is_404(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client

    response = client.get(f"{ADMIN}/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"


def test_admin_list_includes_inactive_rows(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    create_category(client, headers, name="غیرفعال", is_active=False)

    response = client.get(ADMIN, headers=headers)

    assert response.status_code == 200
    assert any(item["is_active"] is False for item in response.json())


def test_patch_updates_and_deactivation_hides_the_row(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    created = create_category(client, headers, name="قبل").json()

    response = client.patch(
        f"{ADMIN}/{created['id']}",
        json={"name": "بعد", "is_active": False, "sort_order": 9},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "بعد"
    assert body["is_active"] is False
    assert body["sort_order"] == 9

    client.cookies.clear()
    public = client.get(PUBLIC).json()
    assert all(item["id"] != created["id"] for item in public)


def test_empty_patch_is_rejected(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    created = create_category(client, headers).json()

    response = client.patch(f"{ADMIN}/{created['id']}", json={}, headers=headers)

    assert response.status_code == 422


def test_patch_cannot_reuse_another_slug(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    taken = unique_slug()
    create_category(client, headers, slug=taken)
    created = create_category(client, headers).json()

    response = client.patch(f"{ADMIN}/{created['id']}", json={"slug": taken}, headers=headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CATEGORY_SLUG_TAKEN"


def test_delete_removes_the_row(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client
    created = create_category(client, headers).json()

    deleted = client.delete(f"{ADMIN}/{created['id']}", headers=headers)
    missing = client.delete(f"{ADMIN}/{created['id']}", headers=headers)

    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_a_write_without_the_csrf_header_is_rejected(
    admin_client: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = admin_client

    response = client.post(
        ADMIN,
        json={"name": f"بدون {uuid.uuid4().hex[:6]}", "slug": unique_slug()},
        headers=headers | {"X-CSRF-Token": ""},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_a_guest_is_unauthenticated_on_every_admin_category_route(
    api_client: TestClient,
    method: str,
) -> None:
    target = ADMIN if method in {"get", "post"} else f"{ADMIN}/{uuid.uuid4()}"

    response = api_client.request(method, target, json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize("role", [Role.CUSTOMER, Role.SALON_OWNER])
@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_non_admin_roles_are_forbidden_on_every_admin_category_route(
    api_client: TestClient,
    create_account: Callable[..., User],
    sign_in_as: Callable[[TestClient, User], None],
    csrf_headers: dict[str, str],
    role: Role,
    method: str,
) -> None:
    sign_in_as(api_client, create_account((role,)))
    target = ADMIN if method in {"get", "post"} else f"{ADMIN}/{uuid.uuid4()}"

    response = api_client.request(method, target, json={}, headers=csrf_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_an_account_with_both_customer_and_admin_is_allowed(
    api_client: TestClient,
    create_account: Callable[..., User],
    sign_in_as: Callable[[TestClient, User], None],
    csrf_headers: dict[str, str],
) -> None:
    sign_in_as(api_client, create_account((Role.CUSTOMER, Role.ADMIN)))

    response = create_category(api_client, csrf_headers)

    assert response.status_code == 201
