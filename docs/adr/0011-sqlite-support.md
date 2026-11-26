# ADR-0011: SQLite as a Supported Local Database

- **Status:** Accepted
- **Date:** 2026-11-25
- **Decision owners:** BeautyBook project owner and engineering agent
- **Supersedes in part:** ADR-0002 (SQLite is no longer limited to lightweight tests)

## Context

The project owner runs BeautyBook on a single machine with a SQLite file. Until now the
application refused every non-PostgreSQL `DATABASE_URL`, so migrations and
`python -m app.cli create-admin` could not run against that database at all. A separate operator
script was the only way to change an administrator, which is why the gap kept resurfacing.

SQLite is genuinely weaker than PostgreSQL for this product: it has no exclusion constraints for
booking intervals, it serialises writers, and it stores timestamps without a timezone. Those
limits matter for the future booking feature, not for the account tables that exist today.

## Decision

- The application accepts two database URLs:
  - `postgresql+psycopg://...` for production, integration tests, and concurrency tests;
  - `sqlite+pysqlite:///...` (or `sqlite:///...`) for a local, single-operator setup.
- The SQLite engine is configured so the application behaves the same way:
  - `PRAGMA foreign_keys=ON` on every connection, so the migration's foreign keys and cascades
    are enforced;
  - `check_same_thread=False`, because synchronous FastAPI endpoints run in worker threads;
  - `UTCDateTime` stores UTC and reads naive SQLite values back as timezone-aware UTC instants,
    so session expiry and keyset pagination never compare naive and aware datetimes. SQLite
    values use one-second precision, matching the migration's `CURRENT_TIMESTAMP` defaults, so a
    cursor compares equal timestamps correctly.
- Alembic runs in batch mode for SQLite, so a future `ALTER` recreates the table instead of
  failing.
- Duplicate-email detection understands both the psycopg constraint name and the SQLite
  `UNIQUE constraint failed: users.email` message.
- The test harness cleans tables with `DELETE` instead of PostgreSQL's `TRUNCATE ... CASCADE`.

## What SQLite does not remove

- PostgreSQL is still required for production and for the booking concurrency and exclusion
  constraint tests (ADR-0003).
- SQLite is single-writer; two simultaneous bookings are not verified by a SQLite test.
- A SQLite deployment is a single-machine setup. It has no network concurrency guarantees.

## Alternatives considered

1. **Keep PostgreSQL-only and change the administrator with a standalone script.** Rejected: the
   application itself could not migrate or run against the owner's database, which is the actual
   problem.
2. **Two configurations and a separate SQLite code path.** Rejected: the same models, services,
   and CLI should run on both databases; only the engine setup differs.
3. **SQLite everywhere, including production booking.** Rejected: it cannot provide the
   interval exclusion constraint or the write concurrency the booking rules require.

## Consequences

Positive:

- The owner can migrate, bootstrap an administrator, and run the API against a local file.
- Integration tests can run without a PostgreSQL service when they do not depend on
  PostgreSQL-only behavior.
- Both backends share one schema and one set of domain rules.

Negative and risks:

- Some behavior differs subtly; `UTCDateTime`, the foreign-key pragma, and the duplicate-email
  fallback exist only to bridge those differences.
- A SQLite deployment must not be presented as production-equivalent for booking correctness.

## References

- ADR-0002, `docs/ARCHITECTURE.md` Section 12, `AGENTS.md` Section 12.
- `backend/app/infrastructure/database.py`, `backend/app/core/config.py`,
  `backend/migrations/env.py`.
