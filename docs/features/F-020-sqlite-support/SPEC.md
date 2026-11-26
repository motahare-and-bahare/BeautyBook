# F-020: SQLite Support and Administrator Bootstrap on SQLite

- **Feature:** SQLite support for the local project database
- **Module:** platform / identity
- **Priority:** P1
- **Status:** In Progress
- **Depends on:** F-001
- **Related ADR:** `docs/adr/0011-sqlite-support.md`

## Problem and objective

The owner runs the project on SQLite, but the backend rejected every non-PostgreSQL
`DATABASE_URL`. As a result `alembic upgrade head` and `python -m app.cli create-admin` could not
run against the owner's database, and administrator changes needed a standalone script.

The objective is that the same code, models, migrations, and CLI run against SQLite with the
same account behavior: migrations apply, `create-admin` creates the owner's administrator, login
and sessions work, and the admin user list paginates.

## In scope

- Accept `sqlite+pysqlite:///...` and `sqlite:///...` in configuration.
- Enforce foreign keys and support the thread model on SQLite.
- Normalize timestamps so SQLite's naive datetimes read back as UTC-aware instants.
- Enable Alembic batch mode for SQLite.
- Recognize SQLite's duplicate-email error.
- Make the test harness cleanup backend-agnostic.
- Document the setup and the `create-admin` command.

## Out of scope

- Booking concurrency and exclusion constraints on SQLite. PostgreSQL remains required.
- WAL mode, backups, or multi-process SQLite deployment.
- Changing the administrator password policy or the role model.

## Functional requirements

1. A SQLite `DATABASE_URL` passes configuration validation; any other scheme is still rejected.
2. `alembic upgrade head` and `alembic downgrade base` work on a SQLite file.
3. `python -m app.cli create-admin --email ... --full-name ...` creates an active account with
   the `admin` and `customer` roles on SQLite; the password is read from the terminal or stdin.
4. Login, session resolution, expiry comparison, and revocation work with SQLite timestamps.
5. A second `create-admin` with the same email fails without changing data.
6. The foreign keys and cascades from migration `0001` are enforced.
7. `GET /api/v1/admin/users` keyset pagination returns every account exactly once.
8. No password or secret is written to the repository.

## Acceptance criteria

- `pytest tests/integration/test_sqlite_support.py` passes.
- The configuration and duplicate-email unit tests pass.
- `ruff check`, `ruff format --check`, and `mypy` are clean.
- The README explains the SQLite setup and the bootstrap command.

## Test strategy

- Unit: configuration URL validation; duplicate-email detection for psycopg and SQLite.
- Integration on a temporary SQLite file: migrations, CLI bootstrap, login, sessions, foreign
  keys, pagination.
- PostgreSQL suite continues to cover integration and concurrency behavior.
