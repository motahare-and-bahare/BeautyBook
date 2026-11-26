# Feature Specification - [F-020] SQLite as the default development database

**Status:** Done (approved directly by the project owner on 2026-11-24)
**Related ADR:** `docs/adr/0011-sqlite-development-default.md` (supersedes ADR-0002 in part)

## 1. Problem and objective

The course this project is delivered for requires SQLite instead of PostgreSQL. Today the
application refuses to start unless `DATABASE_URL` begins with `postgresql+psycopg://`, the test
suite skips or fails without a running PostgreSQL server, and two code paths are PostgreSQL-specific:

- duplicate-email detection reads `psycopg`'s `error.orig.diag.constraint_name`;
- the test fixture clears tables with `TRUNCATE ... CASCADE`.

Objective: make a local SQLite file the **default** database for the application and the test suite,
so a fresh checkout runs with no database server, while keeping PostgreSQL as an explicitly
configured profile for production and for the concurrency/authorization evidence.

The API contract must not change. Registration, login, `/auth/me`, CSRF, session expiry, and error
codes must behave identically on both backends.

## 2. Actors and permissions

- **Developer / student:** runs migrations, the server, and tests without installing PostgreSQL.
- **CI:** runs both profiles - SQLite by default, PostgreSQL for the concurrency path.
- **Production operator:** must configure PostgreSQL; the application refuses SQLite when
  `APP_ENV=production`.

No end user sees a difference. This feature does not change authorization, ownership, or the HTTP
contract.

## 3. User journeys

### Primary journey

1. `cd backend`
2. `alembic upgrade head` creates `backend/beautybook.db` and applies `0001`.
3. `uvicorn app.main:app` starts and `/ready` reports the database healthy.
4. A customer registers, signs in, and calls `/auth/me`; all three succeed.
5. `pytest` runs the whole suite against a throwaway SQLite file without a server.

### Alternative paths

- The developer keeps PostgreSQL: set `TEST_DATABASE_URL` (and `DATABASE_URL`) to
  `postgresql+psycopg://...`; every existing test runs unchanged.
- An in-memory URL (`sqlite://`) is accepted for ad-hoc unit work.

### Failure paths

- `APP_ENV=production` with a SQLite URL: startup fails with a clear validation error.
- An unsupported scheme (`mysql://...`): startup fails with a clear validation error.
- A locked database under concurrent writes: the request waits up to `busy_timeout` and then fails
  as a normal database error; it never returns a false success.

## 4. Scope

### In scope

- `app/core/config.py`: accept SQLite and PostgreSQL URLs; reject everything else; refuse SQLite in
  production; provide a development default for `database_url`.
- `app/infrastructure/database.py`: a shared `build_engine` used by the app and the tests, with
  SQLite pragmas (`foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout`, `synchronous=NORMAL`) and
  `check_same_thread=False`.
- A `UtcDateTime` type that returns timezone-aware UTC values on every backend.
- `app/modules/identity/service.py`: dialect-neutral duplicate-email detection.
- `tests/conftest.py`: default SQLite test database, dialect-neutral table cleanup, shared engine.
- `.env` and `.env.example`.
- New tests for the SQLite profile.
- CI: keep the PostgreSQL job, add a SQLite job that uses the default profile.
- Documentation: ADR-0011, SPEC/PLAN, README, ARCHITECTURE, AGENTS, Task-List.

### Out of scope

- Production on SQLite. It stays forbidden.
- A SQLite replacement for the PostgreSQL exclusion constraint (F-009 owns that design).
- Dropping `psycopg` or the PostgreSQL test path.
- Migrating existing PostgreSQL data into the local file.
- Rewriting migration `0001` or adding SQLite-specific SQL to business logic.

### Non-goals

- Encryption at rest for the local file.
- A database abstraction layer beyond what SQLAlchemy already provides.

## 5. Functional requirements

- **FR-DB-001 (Must):** `DATABASE_URL` and `TEST_DATABASE_URL` accept SQLite URLs and
  `postgresql+psycopg://` URLs.
- **FR-DB-002 (Must):** Any other scheme is rejected at startup with a message naming the accepted
  schemes.
- **FR-DB-003 (Must):** When `APP_ENV=production`, a SQLite URL is rejected.
- **FR-DB-004 (Must):** `database_url` has a development default (`sqlite:///./beautybook.db`) so a
  fresh checkout starts without a `.env` file; an explicit environment value always wins.
- **FR-DB-005 (Must):** The SQLite engine enables foreign keys, WAL journaling, a non-zero busy
  timeout, and allows cross-thread use for the test client.
- **FR-DB-006 (Must):** Datetimes read from any backend are timezone-aware UTC, so session expiry
  comparison never mixes naive and aware values.
- **FR-DB-007 (Must):** Duplicate-email detection works on SQLite and PostgreSQL and still returns
  `409 EMAIL_ALREADY_REGISTERED`.
- **FR-DB-008 (Must):** The test suite runs on SQLite with no PostgreSQL server, and still runs on
  PostgreSQL when `TEST_DATABASE_URL` says so.
- **FR-DB-009 (Must):** Foreign keys are actually enforced on SQLite, so deleting a user removes its
  roles, sessions, and application.
- **FR-DB-010 (Should):** CI proves both profiles: one job on SQLite, one on PostgreSQL.

## 6. Business rules and invariants

- SQLite is a **development and test** backend only (`AGENTS.md` Section 12, ADR-0011).
- The relative SQLite path is resolved from the process working directory; the documented working
  directory is `backend/`.
- The application layer never handles naive datetimes, regardless of backend.
- No SQLite-only SQL appears in `domain.py`, `service.py`, or `repository.py`.
- The HTTP contract, status codes, and error codes are identical on both backends.
- Local database files and their WAL sidecars never enter version control.

## 7. UX and API behavior

### UI

No change. The frontend still calls the same endpoints.

### API

No change. A registration race still returns `201` for the winner and `409
EMAIL_ALREADY_REGISTERED` for the loser. An expired session still returns `401 UNAUTHENTICATED`.

## 8. Data impact

- No schema change. Migration `0001` already emits portable DDL.
- New local artifacts: `backend/beautybook.db` (application) and `backend/beautybook_test.db`
  (tests), plus `-wal` and `-shm` sidecars.
- `.gitignore` must ignore the sidecars as well as `*.db`.
- The existing PostgreSQL data is not copied.

## 9. Security and privacy

- The SQLite file holds password hashes and session hashes in plaintext on disk. It must stay out of
  git and out of any shared folder.
- The production guard prevents an accidental production deployment on SQLite.
- No secret is added to the URL or to the repository.
- `check_same_thread=False` is limited to SQLite, where the driver otherwise refuses the test
  client's threads.

## 10. Edge cases

- WAL leaves `-wal` and `-shm` files next to the database; they must be ignored by git.
- Two threads writing concurrently: `busy_timeout` gives the writer time; a timeout is a normal
  error, never a false success.
- `sqlite://` (memory) works for ad-hoc use but does not persist between connections.
- Running commands from the repository root instead of `backend/` creates the file in another
  directory; documented explicitly.
- `alembic check` must report no drift after the datetime type change on both backends.
- An existing PostgreSQL schema is unaffected; no new migration is required.

## 11. Acceptance criteria

### AC-1

With no `DATABASE_URL` in the environment, `Settings()` resolves `database_url` to
`sqlite:///./beautybook.db` and `app_env` to `development`.

### AC-2

`Settings(database_url="mysql://x")` raises a validation error that names SQLite and
`postgresql+psycopg`.

### AC-3

`Settings(app_env="production", database_url="sqlite:///x.db")` raises a validation error.

### AC-4

The SQLite engine reports `PRAGMA foreign_keys = 1`, `PRAGMA journal_mode = wal`, and a busy
timeout greater than zero.

### AC-5

Deleting a user through the ORM removes its `user_roles`, `sessions`, and `owner_applications` rows
on SQLite, proving foreign-key enforcement.

### AC-6

A datetime written as aware UTC and read back has `tzinfo` set and equals the original instant, on
SQLite and on PostgreSQL.

### AC-7

The full backend suite passes with no `TEST_DATABASE_URL` and no PostgreSQL server, and separately
passes with `TEST_DATABASE_URL` pointing at PostgreSQL.

### AC-8

A duplicate registration on SQLite returns `409 EMAIL_ALREADY_REGISTERED`, and a valid registration
followed by login and `/auth/me` returns `201`, `200`, and `200`.

### AC-9

`alembic upgrade head` creates `backend/beautybook.db`, and `/ready` returns `200` with
`database: ok`.

### AC-10

`ruff check`, `ruff format --check`, and `mypy` are clean.

## 12. Test strategy

- **Unit:** configuration validation (accepted schemes, production guard, development default).
- **Integration (SQLite):** pragmas, foreign-key cascade, UTC round-trip, readiness, duplicate email,
  register plus login plus `/auth/me`.
- **Integration (PostgreSQL):** the same suite via `TEST_DATABASE_URL`, plus the existing
  concurrency test; this is where concurrency evidence lives.
- **Migration:** `alembic upgrade head` and `alembic check` on SQLite; PostgreSQL upgrade remains in
  CI.
- **Manual:** start the server from `backend/`, register a customer, sign in, confirm the file exists.

## 13. Dependencies and open questions

### Dependencies

- F-001 authentication slice (implemented).
- ADR-0011 for the stack change.

### Open questions

- None blocking. Whether SQLite should ever back a production deployment is answered: no.
  The F-009 concurrency design on SQLite (if PostgreSQL is unavailable) remains open and is recorded
  as a follow-up, not silently resolved here.

## 14. Decision log

- 2026-11-24: SQLite becomes the default development and test backend because the course requires
  it; PostgreSQL remains the production database and the only place where concurrency is claimed.
  Trade-off: local behaviour no longer matches production in locking and type semantics, so those
  differences are isolated behind one engine builder and one datetime type.
- 2026-11-24: A custom `UtcDateTime` type is used instead of normalizing at each call site. Reason:
  one place, no missed read path. Trade-off: one more indirection in the model layer.
- 2026-11-24: Duplicate-email detection reads the constraint name first and falls back to the driver
  message. Reason: keep one behaviour on both backends without parsing SQL in business logic.

## 15. Definition of Ready

- Registered in `Task-List.md` as F-020.
- `SPEC.md` and `PLAN.md` exist with testable acceptance criteria.
- ADR-0011 records the stack change and its limits.
- PostgreSQL is available on this machine for the optional profile, so both paths can be verified.
