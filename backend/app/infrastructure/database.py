"""Database engine, session factory, the declarative base, and the UTC datetime type.

The engine is created lazily on first use so importing the application never opens a
connection.

PostgreSQL is the production database. SQLite is supported for a local, single-operator setup
and for tests (ADR-0011), so this module hides the three differences that matter to the rest of
the application:

* SQLite does not enforce foreign keys unless each connection enables the pragma.
* SQLite has no timezone-aware type; it stores a naive UTC string and returns a naive
  ``datetime``. ``UTCDateTime`` returns an aware UTC value so comparisons never mix naive and
  aware instants.
* FastAPI runs synchronous endpoints in worker threads, and PySQLite refuses connections shared
  across threads unless ``check_same_thread`` is disabled.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, TypeDecorator, create_engine, event
from sqlalchemy.dialects.sqlite import DATETIME as SQLITE_DATETIME
from sqlalchemy.engine import Dialect, Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.sql.type_api import TypeEngine

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy 2.x typed models."""


class UTCDateTime(TypeDecorator[datetime]):
    """Store instants in UTC and always read them back timezone-aware.

    PostgreSQL already returns aware values for ``timestamptz``. SQLite stores the value without
    an offset, so a naive result is interpreted as UTC. Writing an instant always converts it to
    UTC first, which keeps both databases consistent regardless of the server's local timezone.

    On SQLite the value is also stored with one-second precision, the same precision as
    ``CURRENT_TIMESTAMP`` used by the migration's server defaults. SQLAlchemy's default format
    adds ``.000000``, so a keyset cursor would compare ``19:32:35.000000`` (bound value) with
    ``19:32:35`` (stored server default) and treat an equal timestamp as greater. Matching the
    server default's format keeps keyset pagination correct.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        if dialect.name == "sqlite":
            return dialect.type_descriptor(
                SQLITE_DATETIME(
                    storage_format=(
                        "%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d"
                    ),
                    regexp=r"(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)",
                )
            )
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def _backend_name(url: str) -> str:
    return make_url(url).get_backend_name()


def create_database_engine(url: str) -> Engine:
    """Build an engine with the settings each backend needs.

    Both the application engine and the test engine use this function, so a test can never pass
    with connection behavior that the running application does not have.
    """

    options: dict[str, Any] = {"pool_pre_ping": True}
    if _backend_name(url) == "sqlite":
        options["connect_args"] = {"check_same_thread": False}

    engine = create_engine(url, **options)

    if _backend_name(url) == "sqlite":

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
            # Off by default in SQLite; without it the cascade and reference rules in the
            # migration would not be enforced.
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return engine


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_database_engine(get_settings().database_url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session and always closes it."""

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
