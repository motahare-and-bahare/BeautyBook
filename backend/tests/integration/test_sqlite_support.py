"""The application runs against SQLite end to end.

SQLite differs from PostgreSQL in three ways that can break an otherwise correct application:
it has no timezone-aware timestamp type, it does not enforce foreign keys unless every
connection enables the pragma, and PySQLite refuses connections shared across threads. These
tests apply the real Alembic migrations to a temporary file and then exercise the administrator
bootstrap command, login, session resolution, the foreign keys, and the keyset-paginated admin
list against it.
"""

from __future__ import annotations

import io
import sqlite3
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.cli import main as cli_main
from app.core.config import get_settings
from app.core.security import verify_password
from app.infrastructure import database
from app.modules.administration import service as administration_service
from app.modules.identity import repository, service
from app.modules.identity.domain import UserStatus
from app.modules.identity.models import User, UserRole

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ADMIN_EMAIL = "motahareborna@gmail.com"
ADMIN_NAME = "Motahare"
PASSWORD = "sqlite-test-password-1384"


@pytest.fixture()
def sqlite_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Engine, Path]]:
    """Create a migrated SQLite file and point the application engine at it."""

    path = tmp_path / "beautybook.db"
    url = f"sqlite+pysqlite:///{path}"

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    # ``%`` is an interpolation character in .ini files.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")

    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", url)
    monkeypatch.setattr(database, "_engine", None)
    monkeypatch.setattr(database, "_session_factory", None)

    engine = database.get_engine()
    try:
        yield engine, path
    finally:
        engine.dispose()


def test_migrations_round_trip_on_sqlite(tmp_path: Path) -> None:
    path = tmp_path / "migrate.db"
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{path}")

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert {"users", "user_roles", "sessions", "owner_applications"} <= tables


def bootstrap_via_cli(monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{PASSWORD}\n"))
    return cli_main(
        [
            "create-admin",
            "--email",
            ADMIN_EMAIL,
            "--full-name",
            ADMIN_NAME,
        ]
    )


def test_create_admin_creates_a_working_administrator_on_sqlite(
    sqlite_database: tuple[Engine, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine, _ = sqlite_database

    assert bootstrap_via_cli(monkeypatch) == 0

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        user = repository.get_user_by_email(session, ADMIN_EMAIL)
        assert user is not None
        assert user.full_name == ADMIN_NAME
        assert user.status == UserStatus.ACTIVE.value
        assert repository.list_roles(session, user.id) == ["admin", "customer"]
        assert verify_password(PASSWORD, user.password_hash)
        # SQLite stores a naive string; the application must read it back as UTC.
        assert user.created_at.tzinfo is not None

        login = service.login(session, email=ADMIN_EMAIL, password=PASSWORD)
        assert login.roles == ("admin", "customer")
        assert login.auth_session.expires_at.tzinfo is not None

        resolved_session, resolved_user = service.resolve_session(
            session,
            login.raw_session_token,
        )
        assert resolved_user.id == user.id
        assert resolved_session.id == login.auth_session.id

        page = administration_service.list_users(session, limit=20)
        assert [item.user.email for item in page.items] == [ADMIN_EMAIL]
        assert page.items[0].roles == ("admin", "customer")
        assert page.items[0].user.created_at.tzinfo is not None


def test_running_create_admin_twice_keeps_one_account(
    sqlite_database: tuple[Engine, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine, _ = sqlite_database

    assert bootstrap_via_cli(monkeypatch) == 0
    assert bootstrap_via_cli(monkeypatch) == 1

    assert "already exists" in capsys.readouterr().err
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(User)) == 1


def test_sqlite_enforces_the_foreign_keys_from_the_migration(
    sqlite_database: tuple[Engine, Path],
) -> None:
    engine, _ = sqlite_database
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with factory() as session:
        session.add(UserRole(user_id=uuid.uuid4(), role="admin"))
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()


def test_the_admin_list_paginates_on_sqlite(
    sqlite_database: tuple[Engine, Path],
) -> None:
    engine, _ = sqlite_database

    with Session(engine, expire_on_commit=False) as session:
        service.create_admin(
            session,
            full_name=ADMIN_NAME,
            email=ADMIN_EMAIL,
            password=PASSWORD,
        )
        for index in (1, 2):
            service.register_customer(
                session,
                full_name=f"Customer {index}",
                email=f"customer{index}@example.com",
                password=PASSWORD,
            )

        first = administration_service.list_users(session, limit=2)
        assert len(first.items) == 2
        assert first.next_cursor is not None

        second = administration_service.list_users(
            session,
            limit=2,
            cursor=first.next_cursor,
        )
        assert len(second.items) == 1
        assert second.next_cursor is None

        seen = [item.user.id for item in (*first.items, *second.items)]
        assert len(set(seen)) == 3
