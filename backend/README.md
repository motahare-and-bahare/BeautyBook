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
- PostgreSQL is the main database; SQLite is only for lightweight tests.
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

Apply the database migration (uses `DATABASE_URL` from `../.env`):

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Run the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Check `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/ready`.

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
