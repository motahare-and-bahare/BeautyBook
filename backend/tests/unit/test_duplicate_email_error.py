"""A duplicate email is recognized on both supported database drivers.

psycopg names the violated constraint on ``orig.diag``; SQLite only puts the table and column in
the exception message. Registration must map both to a 409, not a 500.
"""

from __future__ import annotations

import sqlite3

from sqlalchemy.exc import IntegrityError

from app.modules.identity.service import _is_duplicate_email


def integrity_error(original: BaseException) -> IntegrityError:
    return IntegrityError("INSERT INTO users ...", {}, original)


def test_postgres_unique_email_violation_is_detected() -> None:
    class Diagnostics:
        constraint_name = "uq_users_email"

    class OriginalError(Exception):
        diag = Diagnostics()

    assert _is_duplicate_email(integrity_error(OriginalError("duplicate key value")))


def test_sqlite_unique_email_violation_is_detected() -> None:
    error = sqlite3.IntegrityError("UNIQUE constraint failed: users.email")

    assert _is_duplicate_email(integrity_error(error))


def test_a_different_sqlite_unique_violation_is_not_an_email_collision() -> None:
    error = sqlite3.IntegrityError("UNIQUE constraint failed: sessions.token_hash")

    assert not _is_duplicate_email(integrity_error(error))


def test_a_foreign_key_violation_is_not_an_email_collision() -> None:
    error = sqlite3.IntegrityError("FOREIGN KEY constraint failed")

    assert not _is_duplicate_email(integrity_error(error))
