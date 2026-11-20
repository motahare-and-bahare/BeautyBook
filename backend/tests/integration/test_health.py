"""Health and readiness endpoints."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.infrastructure.database import get_session
from app.main import create_app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


class BrokenSession:
    """Stands in for a database session whose connection is unusable."""

    def execute(self, *args: object, **kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("database is down"))


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_health_does_not_require_the_database() -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: BrokenSession()

    with TestClient(app) as database_down_client:
        response = database_down_client.get("/health")

    assert response.status_code == 200


def test_ready_reports_the_database(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_ready_returns_503_when_the_database_is_unavailable() -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: BrokenSession()

    with TestClient(app) as database_down_client:
        response = database_down_client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert body["error"]["request_id"]
