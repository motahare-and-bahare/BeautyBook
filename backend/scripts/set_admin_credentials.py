#!/usr/bin/env python3
"""Change an existing administrator's email, display name, and password.

Why this script exists
----------------------
``python -m app.cli create-admin`` goes through the application's configuration, and that
configuration only accepts a PostgreSQL URL (ADR-0002). A local SQLite database therefore cannot
be opened by the normal CLI, but developers still need to correct the administrator account in
their own SQLite file. This operator script talks to SQLite directly.

What it does
------------
* finds exactly one account that holds the ``admin`` role (or the one you name),
* validates the new email, name, and password with the same domain rules the application uses,
* stores a fresh Argon2id hash with the application's default cost parameters,
* revokes that account's active sessions, because the password changed,
* and verifies the new password against the stored hash before committing.

The password is read from the terminal (or from standard input when piped). It is never a
command-line argument, so it does not end up in shell history or the process list.

Usage (from ``backend/``, venv active)::

    python scripts/set_admin_credentials.py \
        --database beautybook.db \
        --email motahareborna@gmail.com \
        --full-name Motahare

Add ``--current-email old@example.com`` when the database holds more than one administrator, and
``--keep-sessions`` to leave existing sessions signed in.
"""

from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

# The domain rules are framework-free, so importing them here stays independent of app settings.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from argon2 import PasswordHasher  # noqa: E402
from argon2.exceptions import InvalidHashError, VerificationError  # noqa: E402

from app.modules.identity.domain import (  # noqa: E402
    DomainValidationError,
    normalize_email,
    normalize_full_name,
    validate_password,
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

ADMIN_ROLE = "admin"

# Ranked from most likely to least likely; the first existing file is used when --database is
# omitted.
DEFAULT_DATABASE_NAMES: tuple[str, ...] = (
    "beautybook.db",
    "beautybook.sqlite3",
    "beautybook.sqlite",
    "app.db",
    "dev.db",
)

# Matches the application defaults in app.core.config so a later sign-in does not immediately
# ask for a rehash.
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4


class ScriptError(Exception):
    """A failure that should be reported to the operator without a traceback."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="set_admin_credentials.py",
        description=(
            "Change the email, display name, and password of an existing administrator in a "
            "SQLite database. The password is read from standard input, never from the "
            "command line."
        ),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help=(
            "Path to the SQLite file. When omitted, DATABASE_URL (if it is a SQLite URL) or a "
            "file named one of the defaults in the current directory is used: "
            f"{', '.join(DEFAULT_DATABASE_NAMES)}."
        ),
    )
    parser.add_argument(
        "--current-email",
        dest="current_email",
        default=None,
        help="Email of the administrator to change. Required when several administrators exist.",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="New email address. It is normalized to lowercase.",
    )
    parser.add_argument(
        "--full-name",
        dest="full_name",
        required=True,
        help="New display name (2-100 characters).",
    )
    parser.add_argument(
        "--keep-sessions",
        dest="keep_sessions",
        action="store_true",
        help="Do not revoke the account's existing sessions after the password change.",
    )
    return parser


def resolve_database_path(explicit: Path | None) -> Path:
    """Return the SQLite file to open, or raise when it cannot be determined."""

    if explicit is not None:
        path = explicit.expanduser()
        if not path.is_file():
            raise ScriptError(f"Database file not found: {path}")
        return path

    import os  # local import keeps the module import cheap

    configured = os.environ.get("DATABASE_URL", "")
    if configured.startswith("sqlite"):
        # Accept sqlite:///relative.db, sqlite:////absolute.db, and sqlite+pysqlite:///...
        _, _, remainder = configured.partition(":///")
        candidate = Path(remainder)
        if candidate.is_file():
            return candidate

    for name in DEFAULT_DATABASE_NAMES:
        candidate = Path.cwd() / name
        if candidate.is_file():
            return candidate

    searched = ", ".join(DEFAULT_DATABASE_NAMES)
    raise ScriptError(
        "Could not find the SQLite database. Pass it explicitly, for example: "
        f"--database {searched.split(',')[0] or 'beautybook.db'}"
    )


def read_password() -> str:
    """Read the new password from the terminal, or from piped standard input."""

    if sys.stdin.isatty():
        first = getpass.getpass("New administrator password: ")
        second = getpass.getpass("Repeat the new password: ")
        if first != second:
            raise ScriptError("The two passwords do not match.")
        return first
    return sys.stdin.readline().rstrip("\r\n")


def has_table(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def find_administrators(connection: sqlite3.Connection) -> list[tuple[str, str, str]]:
    """Return ``(id, email, full_name)`` for every account holding the admin role."""

    return list(
        connection.execute(
            """
            SELECT u.id, u.email, u.full_name
            FROM users AS u
            JOIN user_roles AS r ON r.user_id = u.id AND r.role = ?
            ORDER BY u.email
            """,
            (ADMIN_ROLE,),
        )
    )


def select_administrator(
    administrators: list[tuple[str, str, str]],
    current_email: str | None,
) -> tuple[str, str, str]:
    """Pick the single administrator to update, explaining any ambiguity."""

    if not administrators:
        raise ScriptError(
            "No account holds the admin role in this database. Create one first with "
            "'python -m app.cli create-admin'."
        )

    if current_email is not None:
        wanted = normalize_email(current_email)
        matches = [row for row in administrators if row[1].lower() == wanted]
        if not matches:
            known = ", ".join(row[1] for row in administrators)
            raise ScriptError(f"No administrator uses {wanted}. Known administrators: {known}")
        if len(matches) > 1:
            raise ScriptError(f"More than one administrator uses {wanted}.")
        return matches[0]

    if len(administrators) > 1:
        known = ", ".join(row[1] for row in administrators)
        raise ScriptError(
            "This database has several administrators. Choose one with --current-email. "
            f"Known administrators: {known}"
        )
    return administrators[0]


def ensure_email_is_free(
    connection: sqlite3.Connection,
    new_email: str,
    user_id: str,
) -> None:
    """Reject a new email that another account already owns."""

    row = connection.execute(
        "SELECT id FROM users WHERE lower(email) = ? AND id <> ?",
        (new_email, user_id),
    ).fetchone()
    if row is not None:
        raise ScriptError(f"Another account already uses {new_email}.")


def hash_new_password(password: str) -> str:
    hasher = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
    )
    return hasher.hash(password)


def verify_new_password(password: str, password_hash: str) -> None:
    hasher = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
    )
    try:
        hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError) as error:  # pragma: no cover - defensive
        raise ScriptError("The new password did not verify against the stored hash.") from error


def sqlite_timestamp() -> str:
    """Return a UTC timestamp in the layout SQLAlchemy's SQLite dialect reads back."""

    return datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")


def run(args: argparse.Namespace) -> int:
    database_path = resolve_database_path(args.database)
    new_email = normalize_email(args.email)
    new_name = normalize_full_name(args.full_name)
    password = read_password()
    validate_password(password)

    # mode=rw makes a wrong path fail loudly instead of silently creating an empty database.
    connection = sqlite3.connect(f"file:{database_path}?mode=rw", uri=True)
    try:
        if not has_table(connection, "users") or not has_table(connection, "user_roles"):
            raise ScriptError(
                f"{database_path} is not a BeautyBook database (expected users and user_roles "
                "tables). Run 'alembic upgrade head' against the right file."
            )

        user_id, old_email, old_name = select_administrator(
            find_administrators(connection),
            args.current_email,
        )
        ensure_email_is_free(connection, new_email, user_id)

        password_hash = hash_new_password(password)
        timestamp = sqlite_timestamp()

        connection.execute(
            """
            UPDATE users
               SET email = ?, full_name = ?, password_hash = ?, updated_at = ?
             WHERE id = ?
            """,
            (new_email, new_name, password_hash, timestamp, user_id),
        )

        revoked = 0
        if not args.keep_sessions and has_table(connection, "sessions"):
            cursor = connection.execute(
                """
                UPDATE sessions
                   SET revoked_at = ?
                 WHERE user_id = ? AND revoked_at IS NULL
                """,
                (timestamp, user_id),
            )
            revoked = cursor.rowcount

        verify_new_password(password, password_hash)
        connection.commit()
    except sqlite3.Error as error:
        connection.rollback()
        raise ScriptError(
            f"SQLite rejected the change: {error}. The database was left unchanged."
        ) from error
    except ScriptError:
        connection.rollback()
        raise
    finally:
        connection.close()

    print(f"Updated administrator {user_id}")
    print(f"  email:      {old_email} -> {new_email}")
    if old_name != new_name:
        print(f"  name:       {old_name} -> {new_name}")
    else:
        print(f"  name:       {new_name} (unchanged)")
    print("  password:   replaced with a new Argon2id hash")
    if args.keep_sessions:
        print("  sessions:   kept (--keep-sessions)")
    else:
        print(f"  sessions:   {revoked} active session(s) revoked")
    print(f"Database: {database_path}")
    print("Sign in with the new email and password.")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return run(args)
    except DomainValidationError as error:
        print(f"error: {error.message}", file=sys.stderr)
        return EXIT_FAILED
    except ScriptError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILED


if __name__ == "__main__":
    raise SystemExit(main())
