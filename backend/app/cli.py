"""BeautyBook administrative command line.

These commands run with direct database access and are deliberately never mounted on the
HTTP application. They are the only way to create an account with the ``admin`` role without
an existing administrator, which is why they require database access and are run by an
operator rather than exposed as an endpoint.

Usage (run from ``backend/``, with ``DATABASE_URL`` configured)::

    python -m app.cli create-admin --email admin@beautybook.com --full-name "Site Admin"

The password is read from the terminal, or from standard input when it is piped. It is never
accepted as a command-line argument, so it cannot leak through shell history or the process
list.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import configure_logging
from app.infrastructure.database import get_session_factory
from app.modules.identity import service
from app.modules.identity.domain import DomainValidationError

DEFAULT_ADMIN_FULL_NAME = "BeautyBook Administrator"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description=(
            "BeautyBook administrative tools. They require database access, are run by an "
            "operator, and are never exposed over HTTP."
        ),
    )

    subcommands = parser.add_subparsers(dest="command", metavar="<command>")

    create_admin = subcommands.add_parser(
        "create-admin",
        help="Create the first administrator account.",
        description=(
            "Create an active administrator with the admin and customer roles. The password is "
            "read from standard input, never from the command line."
        ),
    )
    create_admin.add_argument(
        "--email",
        required=True,
        help="Email address of the administrator. It is normalized to lowercase.",
    )
    create_admin.add_argument(
        "--full-name",
        dest="full_name",
        default=DEFAULT_ADMIN_FULL_NAME,
        help=f"Display name (default: {DEFAULT_ADMIN_FULL_NAME!r}).",
    )
    create_admin.set_defaults(handler=run_create_admin)

    return parser


def read_password() -> str:
    """Read the administrator password from the terminal or from standard input.

    A hidden prompt is used when a terminal is attached. When standard input is piped (for
    example in a deployment script) the first line is used instead. The value never becomes
    part of ``sys.argv``.
    """

    if sys.stdin.isatty():
        return getpass.getpass("Administrator password: ")
    return sys.stdin.readline().rstrip("\r\n")


def run_create_admin(args: argparse.Namespace) -> int:
    """Create the first administrator and report the outcome without leaking secrets."""

    password = read_password()
    session: Session | None = None

    try:
        session = get_session_factory()()
        result = service.create_admin(
            session,
            full_name=args.full_name,
            email=args.email,
            password=password,
        )
    except DomainValidationError as error:
        _fail(error.message)
        return EXIT_FAILED
    except service.EmailAlreadyRegisteredError:
        _fail("An account with this email already exists. Choose another email address.")
        return EXIT_FAILED
    except OperationalError:
        _fail(
            "The database is not reachable. Check DATABASE_URL and run the migrations first "
            "(alembic upgrade head)."
        )
        return EXIT_FAILED
    except SQLAlchemyError:
        _fail(
            "The database rejected the write. Apply the migrations (alembic upgrade head) and "
            "check the application logs."
        )
        return EXIT_FAILED
    finally:
        if session is not None:
            session.close()

    print(
        f"Created administrator {result.user.email} "
        f"(id={result.user.id}) with roles: {', '.join(result.roles)}."
    )
    print("Sign in with this email and the password you just entered.")
    return EXIT_OK


def _fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handler: Callable[[argparse.Namespace], int] | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE

    configure_logging()
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
