"""Database engine, session factory, and the declarative base.

The engine is created lazily on first use so importing the application never opens a
connection. Models arrive in F-001 Step 2 and will use :class:`Base`.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy 2.x typed models."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(get_settings().database_url, pool_pre_ping=True)
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
