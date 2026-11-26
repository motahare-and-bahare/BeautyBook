# ADR-0011: SQLite as the Development Default, PostgreSQL Retained for Production and Concurrency

- **Status:** Accepted
- **Date:** 2026-11-24
- **Decision owners:** BeautyBook project owner (course requirement), engineering agent
- **Supersedes:** ADR-0002 in part - only the "PostgreSQL is also the local development database and
  the test-suite database" part. ADR-0002's production and concurrency rules still stand.

## Context

ADR-0002 chose PostgreSQL for development, integration tests, and production, and rejected "SQLite
locally, PostgreSQL in production" because it lets the team rely on behaviour that production does
not have. That reasoning is still correct for booking concurrency.

The delivery requirement for this project changed: the course requires SQLite. The product is also
not yet at F-009; today the persistence layer only stores accounts, roles, sessions, and owner
applications, which are portable.

Two facts make a controlled switch possible without pretending the gap does not exist:

1. Every PostgreSQL-specific behaviour that matters for correctness is already isolated or can be
   isolated in one place.
2. PostgreSQL can stay in the project - and in CI - as an explicit profile, so the concurrency
   evidence is still produced on the database that will run in production.

## Decision

- SQLite is the **default** database for local development and for the default test profile, using a
  file at `backend/beautybook.db` (`backend/beautybook_test.db` for tests).
- PostgreSQL remains the **only** production database and the **only** backend on which
  concurrency correctness may be claimed.
- SQLite URLs are rejected when `APP_ENV=production`.
- `postgresql+psycopg://` stays a first-class profile; selecting it runs the identical test suite,
  including the registration race test.
- Differences are handled in exactly two places:
  - `app/infrastructure/database.py`: one engine builder that applies SQLite pragmas
    (`foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout`, `synchronous=NORMAL`) and one
    `UtcDateTime` type that always returns aware UTC values;
  - `app/modules/identity/service.py`: duplicate-email detection that reads the constraint name and
    falls back to the driver message.
- CI runs both profiles: a SQLite job that uses the defaults, and the existing PostgreSQL job.
- No SQLite-specific SQL enters `domain.py`, `service.py`, or `repository.py`.

## Alternatives considered

1. **Keep PostgreSQL only.** Rejected: the course requirement is explicit and the owner approved the
   change.
2. **SQLite everywhere, including production.** Rejected: it cannot enforce the interval exclusion
   constraint needed by F-009, has weaker concurrency, and `AGENTS.md` forbids it. It would also make
   the double-booking guarantee unprovable.
3. **SQLite default with no PostgreSQL profile.** Rejected: it would delete the only environment in
   which the booking guarantee can be tested, and the deletion would be hard to reverse later.
4. **In-memory SQLite for tests only, file for the app.** Rejected as the default: in-memory
   databases need a static pool and behave differently across threads, which hides exactly the
   problems this ADR is trying to surface.

## Consequences

Positive:

- A fresh checkout runs with no database server: `alembic upgrade head` and `uvicorn` are enough.
- The whole suite runs in seconds on a file, which keeps the TDD loop short.
- The PostgreSQL path, the migration, and the concurrency evidence survive.
- The portability hazards (naive datetimes, disabled foreign keys, driver-specific error inspection)
  are now covered by tests instead of being latent.

Negative and risks:

- Local behaviour no longer matches production in locking, type semantics, and `ALTER TABLE`
  support. Alembic batch mode will be required for future SQLite schema changes that alter columns.
- SQLite stores timestamps without a timezone; correctness depends on the `UtcDateTime` type, not on
  the column type. Any new datetime column must use it.
- A single-writer database can produce "database is locked" under load; `busy_timeout` reduces it
  but does not remove it.
- The local file contains password and session hashes in plaintext and must never be committed or
  shared.

Follow-up:

- F-009 must record how the overlap guarantee is enforced and tested on PostgreSQL, and must not
  claim SQLite equivalence.
- If SQLite becomes the only available backend in some environment, the concurrency verification is
  reported as **not run**, never as passed.
- Add Alembic `render_as_batch=True` for SQLite when the first column-altering migration appears.

## References

- `AGENTS.md`, Sections 5, 10, and 12.
- `docs/ARCHITECTURE.md`, Sections 11-12.
- `docs/features/F-020-sqlite-default-database/SPEC.md` and `PLAN.md`.
- ADR-0002 (partially superseded), ADR-0003 (booking concurrency, unchanged).
