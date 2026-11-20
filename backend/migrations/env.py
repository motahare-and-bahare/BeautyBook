"""Alembic environment.

The database URL comes from the Alembic configuration when a caller provides one (tests do),
otherwise from the validated application settings. Models are imported so their metadata is
available for future autogeneration.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.infrastructure.database import Base
from app.modules.identity import models  # noqa: F401 - registers the metadata

config = context.config


def _database_url() -> str:
    configured = config.get_main_option("sqlalchemy.url")
    return configured if configured else get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
