"""CSRF issuance and enforcement against a real application."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app
from app.modules.identity.dependencies import require_csrf

CSRF_PATH = "/api/v1/auth/csrf"
PROTECTED_PATH = "/__test__/csrf-protected"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def issue_token(client: TestClient) -> str:
    response = client.get(CSRF_PATH)
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert isinstance(token, str)
    return token


def protected_client(calls: list[str]) -> TestClient:
    app = create_app()

    @app.post(PROTECTED_PATH, dependencies=[Depends(require_csrf)])
    def protected_route() -> dict[str, str]:
        calls.append("called")
        return {"status": "accepted"}

    return TestClient(app)


def test_csrf_endpoint_returns_the_token_and_a_readable_cookie(client: TestClient) -> None:
    settings = get_settings()

    response = client.get(CSRF_PATH)

    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert len(token) >= 32

    set_cookie = response.headers["set-cookie"]
    lowered = set_cookie.lower()
    assert f"{settings.csrf_cookie_name}={token}" in set_cookie
    assert client.cookies.get(settings.csrf_cookie_name) == token
    assert "httponly" not in lowered
    assert "samesite=lax" in lowered
    assert "path=/" in lowered
    assert "max-age=" in lowered


def test_each_request_rotates_the_token(client: TestClient) -> None:
    assert issue_token(client) != issue_token(client)


def test_missing_header_is_rejected_before_the_handler_runs() -> None:
    calls: list[str] = []

    with protected_client(calls) as client:
        issue_token(client)
        response = client.post(PROTECTED_PATH)

    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "CSRF_INVALID"
    assert error["request_id"]
    assert calls == []


def test_mismatched_header_is_rejected_before_the_handler_runs() -> None:
    calls: list[str] = []
    settings = get_settings()

    with protected_client(calls) as client:
        token = issue_token(client)
        response = client.post(
            PROTECTED_PATH,
            headers={settings.csrf_header_name: f"{token}x"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"
    assert calls == []


def test_a_header_without_the_cookie_is_rejected() -> None:
    calls: list[str] = []
    settings = get_settings()

    with protected_client(calls) as client:
        response = client.post(
            PROTECTED_PATH,
            headers={settings.csrf_header_name: "a" * 43},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_INVALID"
    assert calls == []


def test_a_valid_cookie_and_header_reach_the_handler() -> None:
    calls: list[str] = []
    settings = get_settings()

    with protected_client(calls) as client:
        token = issue_token(client)
        response = client.post(
            PROTECTED_PATH,
            headers={settings.csrf_header_name: token},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    assert calls == ["called"]
