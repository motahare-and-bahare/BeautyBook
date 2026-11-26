"""The SQLite operator script changes the administrator account and nothing else.

These tests build a throwaway SQLite file with the columns the script touches, run the script as
an operator would (through a subprocess, with the password on standard input), and inspect the
result. They do not import the application settings, which is the point of the script.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from argon2 import PasswordHasher

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "set_admin_credentials.py"

OLD_PASSWORD_HASH = "argon2id$v=19$m=65536,t=3,p=4$placeholder$placeholder"
NEW_PASSWORD = "AdminBootstrap!1384"

SCHEMA = """
CREATE TABLE users (
    id VARCHAR(32) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
CREATE TABLE user_roles (
    user_id VARCHAR(32) NOT NULL,
    role VARCHAR(20) NOT NULL,
    PRIMARY KEY (user_id, role)
);
CREATE TABLE sessions (
    id VARCHAR(32) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    created_at DATETIME NOT NULL
);
"""


@pytest.fixture()
def database(tmp_path: Path) -> Path:
    path = tmp_path / "beautybook.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO users (id, full_name, email, password_hash, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            ("admin-1", "Site Administrator", "admin@beautybook.com", OLD_PASSWORD_HASH),
        )
        connection.execute("INSERT INTO user_roles (user_id, role) VALUES ('admin-1', 'admin')")
        connection.execute("INSERT INTO user_roles (user_id, role) VALUES ('admin-1', 'customer')")
        connection.execute(
            "INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at)"
            " VALUES (?, 'admin-1', ?, '2030-01-01 00:00:00', CURRENT_TIMESTAMP)",
            (uuid.uuid4().hex, "a" * 64),
        )
    return path


def run_script(
    database: Path, *arguments: str, password: str = NEW_PASSWORD
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--database",
            str(database),
            *arguments,
        ],
        input=password + "\n",
        capture_output=True,
        text=True,
        check=False,
    )


def read_admin(database: Path) -> tuple[str, str, str]:
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT email, full_name, password_hash FROM users WHERE id = 'admin-1'"
        ).fetchone()
    assert row is not None
    return str(row[0]), str(row[1]), str(row[2])


def test_updates_email_name_and_password(database: Path) -> None:
    result = run_script(
        database,
        "--email",
        "MotahareBorna@gmail.com ",
        "--full-name",
        "Motahare",
    )

    assert result.returncode == 0, result.stderr
    email, name, password_hash = read_admin(database)
    assert email == "motahareborna@gmail.com"
    assert name == "Motahare"
    assert password_hash != OLD_PASSWORD_HASH
    assert PasswordHasher().verify(password_hash, NEW_PASSWORD) is True
    assert "motahareborna@gmail.com" in result.stdout


def test_revokes_active_sessions_and_keeps_the_roles(database: Path) -> None:
    result = run_script(database, "--email", "new@example.com", "--full-name", "New Name")
    assert result.returncode == 0, result.stderr

    with sqlite3.connect(database) as connection:
        revoked = connection.execute(
            "SELECT revoked_at FROM sessions WHERE user_id = 'admin-1'"
        ).fetchall()
        roles = connection.execute(
            "SELECT role FROM user_roles WHERE user_id = 'admin-1' ORDER BY role"
        ).fetchall()

    assert len(revoked) == 1
    assert revoked[0][0] is not None
    assert [row[0] for row in roles] == ["admin", "customer"]


def test_keep_sessions_leaves_them_signed_in(database: Path) -> None:
    result = run_script(
        database,
        "--email",
        "new@example.com",
        "--full-name",
        "New Name",
        "--keep-sessions",
    )

    assert result.returncode == 0, result.stderr
    with sqlite3.connect(database) as connection:
        revoked_at = connection.execute("SELECT revoked_at FROM sessions").fetchone()[0]
    assert revoked_at is None


def test_rejects_a_password_shorter_than_the_policy(database: Path) -> None:
    result = run_script(
        database,
        "--email",
        "new@example.com",
        "--full-name",
        "New Name",
        password="short",
    )

    assert result.returncode == 1
    assert "12-128" in result.stderr
    assert read_admin(database) == ("admin@beautybook.com", "Site Administrator", OLD_PASSWORD_HASH)


def test_rejects_an_invalid_email_without_writing(database: Path) -> None:
    result = run_script(database, "--email", "not-an-email", "--full-name", "New Name")

    assert result.returncode == 1
    assert "valid email" in result.stderr
    assert read_admin(database)[0] == "admin@beautybook.com"


def test_rejects_an_email_owned_by_another_account(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO users (id, full_name, email, password_hash, created_at, updated_at)"
            " VALUES ('customer-1', 'Customer', 'taken@example.com', ?, CURRENT_TIMESTAMP,"
            " CURRENT_TIMESTAMP)",
            (OLD_PASSWORD_HASH,),
        )

    result = run_script(database, "--email", "taken@example.com", "--full-name", "New Name")

    assert result.returncode == 1
    assert "already uses" in result.stderr
    assert read_admin(database)[0] == "admin@beautybook.com"


def test_requires_current_email_when_several_administrators_exist(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO users (id, full_name, email, password_hash, created_at, updated_at)"
            " VALUES ('admin-2', 'Second Admin', 'second@beautybook.com', ?, CURRENT_TIMESTAMP,"
            " CURRENT_TIMESTAMP)",
            (OLD_PASSWORD_HASH,),
        )
        connection.execute("INSERT INTO user_roles (user_id, role) VALUES ('admin-2', 'admin')")

    ambiguous = run_script(database, "--email", "new@example.com", "--full-name", "New Name")
    assert ambiguous.returncode == 1
    assert "--current-email" in ambiguous.stderr

    chosen = run_script(
        database,
        "--email",
        "new@example.com",
        "--full-name",
        "New Name",
        "--current-email",
        "second@beautybook.com",
    )
    assert chosen.returncode == 0, chosen.stderr

    with sqlite3.connect(database) as connection:
        first = connection.execute("SELECT email FROM users WHERE id = 'admin-1'").fetchone()[0]
        second = connection.execute("SELECT email FROM users WHERE id = 'admin-2'").fetchone()[0]
    assert first == "admin@beautybook.com"
    assert second == "new@example.com"


def test_reports_a_missing_database_file(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--database",
            str(tmp_path / "missing.db"),
            "--email",
            "new@example.com",
            "--full-name",
            "New Name",
        ],
        input=NEW_PASSWORD + "\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "not found" in result.stderr
    assert not (tmp_path / "missing.db").exists()


def test_reports_a_database_without_the_expected_tables(tmp_path: Path) -> None:
    path = tmp_path / "empty.db"
    with sqlite3.connect(path):
        pass

    result = run_script(path, "--email", "new@example.com", "--full-name", "New Name")

    assert result.returncode == 1
    assert "not a BeautyBook database" in result.stderr
