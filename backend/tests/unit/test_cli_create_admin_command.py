"""The create-admin command is thin: it reads the password safely and reports the outcome.

These tests use a fake database session so they run without PostgreSQL. The real persistence is
covered by ``tests/integration/test_cli_create_admin.py``.
"""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from app.cli import main
from app.modules.identity import service
from app.modules.identity.domain import DomainValidationError

ADMIN_EMAIL = "admin@beautybook.com"
PASSWORD = "correct horse battery staple"


class FakeSession:
    """Records instances so a test can prove the session is always closed."""

    instances: list[FakeSession] = []

    def __init__(self) -> None:
        self.closed = False
        FakeSession.instances.append(self)

    def close(self) -> None:
        self.closed = True


def install_fake_database(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSession.instances.clear()
    monkeypatch.setattr("app.cli.get_session_factory", lambda: FakeSession)


def install_create_admin(
    monkeypatch: pytest.MonkeyPatch,
    behaviour: object,
) -> dict[str, str]:
    """Replace the use case with a recorder and return the captured calls."""

    captured: dict[str, str] = {}

    def fake_create_admin(
        session: FakeSession,
        *,
        full_name: str,
        email: str,
        password: str,
    ) -> service.AdminBootstrap:
        captured.update(full_name=full_name, email=email, password=password)
        if isinstance(behaviour, Exception):
            raise behaviour
        return service.AdminBootstrap(
            user=SimpleNamespace(id="user-1", email=email),  # type: ignore[arg-type]
            roles=("admin", "customer"),
        )

    monkeypatch.setattr("app.cli.service.create_admin", fake_create_admin)
    return captured


def test_password_cannot_be_passed_as_an_argument() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["create-admin", "--email", ADMIN_EMAIL, "--password", PASSWORD])

    assert exit_info.value.code == 2


def test_password_is_read_from_stdin_and_never_printed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_database(monkeypatch)
    captured = install_create_admin(monkeypatch, behaviour=None)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{PASSWORD}\n"))

    exit_code = main(["create-admin", "--email", ADMIN_EMAIL])

    output = capsys.readouterr()
    assert exit_code == 0
    assert captured["password"] == PASSWORD
    assert captured["email"] == ADMIN_EMAIL
    assert PASSWORD not in output.out
    assert PASSWORD not in output.err
    assert ADMIN_EMAIL in output.out


def test_the_session_is_always_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_database(monkeypatch)
    install_create_admin(monkeypatch, behaviour=service.EmailAlreadyRegisteredError())
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{PASSWORD}\n"))

    main(["create-admin", "--email", ADMIN_EMAIL])

    assert [session.closed for session in FakeSession.instances] == [True]


def test_a_rejected_password_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_database(monkeypatch)
    install_create_admin(
        monkeypatch,
        behaviour=DomainValidationError(
            "INVALID_PASSWORD",
            "The password must be 12-128 characters and must not be blank.",
            "password",
        ),
    )
    monkeypatch.setattr("sys.stdin", io.StringIO("short\n"))

    exit_code = main(["create-admin", "--email", ADMIN_EMAIL])

    assert exit_code == 1
    assert "12-128" in capsys.readouterr().err


def test_a_duplicate_email_returns_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_database(monkeypatch)
    install_create_admin(monkeypatch, behaviour=service.EmailAlreadyRegisteredError())
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{PASSWORD}\n"))

    exit_code = main(["create-admin", "--email", ADMIN_EMAIL])

    assert exit_code == 1
    assert "already exists" in capsys.readouterr().err


def test_no_subcommand_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "create-admin" in capsys.readouterr().out
