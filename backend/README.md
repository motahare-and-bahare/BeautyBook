# Backend

FastAPI application for BeautyBook. The F-001 foundation is implemented: configuration
validation, request IDs, the error envelope, the lazy database engine, health/readiness checks,
and the administrative CLI boundary. Authentication, roles, sessions, and owner applications are
added by the remaining F-001 steps.

## Planned structure

```text
backend/
├── app/
│   ├── api/v1/            # Router composition for /api/v1
│   ├── core/              # Config, security, errors, logging, request IDs
│   ├── modules/           # Domain modules
│   │   ├── identity/
│   │   ├── users/
│   │   ├── salons/
│   │   ├── services/
│   │   ├── portfolio/
│   │   ├── availability/
│   │   ├── bookings/
│   │   ├── notifications/
│   │   └── administration/
│   ├── infrastructure/    # Database session, email, storage adapters
│   └── main.py            # Added in F-001
├── migrations/            # Alembic
└── tests/
    ├── unit/
    ├── integration/
    └── concurrency/
```

Each module will use a consistent internal layout:

```text
modules/<module>/
├── domain.py       # Framework-free rules and policies
├── models.py       # SQLAlchemy 2.x mappings
├── schemas.py      # Pydantic request/response schemas
├── repository.py   # Persistence queries
├── service.py      # Use cases and transaction boundaries
└── router.py       # HTTP endpoints only
```

## Rules

- Routers contain no business rules.
- Services own transactions and authorization.
- Domain code imports no FastAPI or SQLAlchemy.
- Modules do not import another module's ORM models.
- PostgreSQL is the production database; SQLite is supported for a local single-operator setup
  and for tests (ADR-0011).
- Every schema change uses Alembic.
- Every protected endpoint has a negative authorization test.
- Never return ORM objects directly.
- Never log secrets or unnecessary personal data.

## Setup

Run from this folder. Python 3.12 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item ..\.env.example ..\.env   # then replace the placeholders
```

On macOS or Linux use `source .venv/bin/activate` and `pip install -e ".[dev]"`.

### Using SQLite instead of PostgreSQL

A single-file SQLite database is supported for local development (ADR-0011). Put one of these in
`../.env` instead of the PostgreSQL URL:

```dotenv
# macOS or Linux
DATABASE_URL=sqlite+pysqlite:///./beautybook.db
# Windows
# DATABASE_URL=sqlite+pysqlite:///C:/path/to/beautybook.db
```

Relative paths resolve against the folder you run the command from, so run the commands below
from `backend/`. The same migrations and the same `create-admin` command work; the engine enables
foreign keys, reads timestamps back as UTC, and accepts FastAPI's worker threads. SQLite does not
provide the booking concurrency and exclusion-constraint guarantees, so those tests still need
PostgreSQL.

Apply the database migration (uses `DATABASE_URL` from `../.env`):

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Check `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/ready`.

## First administrator (bootstrap)

Administrator accounts are never created through the HTTP API. Create the first one once, after
applying the migrations:

```powershell
.\.venv\Scripts\python.exe -m app.cli create-admin --email admin@beautybook.com --full-name "Site Administrator"
```

On macOS or Linux use `.venv/bin/python`. The password is read from the terminal. When standard
input is piped, the first line is used instead, so no password ever appears in `argv`:

```bash
printf '%s\n' 'a-long-password-of-at-least-12-characters' \
  | .venv/bin/python -m app.cli create-admin --email admin@beautybook.com
```

The account is created active with the `admin` and `customer` roles in one commit. A duplicate
email is refused without changing data, and a password outside the 12-128 character policy is
rejected before anything is written. The command uses `DATABASE_URL`, so it works against both
PostgreSQL and SQLite.

### Changing an administrator in a SQLite development database

To change an account that already exists, use the operator script. It talks to the SQLite file
directly, so it also works when the application settings are not configured:

```powershell
.\.venv\Scripts\python.exe scripts\set_admin_credentials.py `
  --database beautybook.db `
  --email motahareborna@gmail.com `
  --full-name Motahare
```

It validates the new email, name, and password with the same domain rules as the application,
stores a fresh Argon2id hash, revokes that account's active sessions, and verifies the new
password against the stored hash before committing. Pass `--current-email` when the database has
more than one administrator and `--keep-sessions` to leave existing sessions signed in. The
password is read from the terminal, or from standard input when piped.

Verify:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

The tests read `DATABASE_URL` from `../.env` or from the environment. Integration tests need a
reachable PostgreSQL database.

See:

- [`../AGENTS.md`](../AGENTS.md)
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
- [`../Task-List.md`](../Task-List.md)
