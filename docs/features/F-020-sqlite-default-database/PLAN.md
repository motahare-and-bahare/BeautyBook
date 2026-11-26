# Implementation Plan - [F-020] SQLite as the default development database

## 1. Implementation approach

Portability change driven by tests. The risky parts are not the URL switch; they are the four
behaviours that differ between the backends:

1. configuration refuses any non-PostgreSQL URL;
2. SQLite returns naive datetimes for `DateTime(timezone=True)`, which breaks session-expiry
   comparison;
3. SQLite does not enforce foreign keys unless a pragma enables them per connection;
4. duplicate-email detection reads a `psycopg`-only attribute.

The plan isolates all four behind `app/infrastructure/database.py` (one engine builder, one datetime
type) and one small function in the identity service, then proves the result with a dedicated
SQLite profile test module.

No schema change and no new migration.

## 2. Preconditions

- F-001 authentication slice is implemented and green on PostgreSQL.
- `backend/.venv` exists.
- PostgreSQL on port 5433 is available for the optional profile verification.

## 3. Ordered TDD tasks

### Test-first order

1. **Red** - rewrite `tests/unit/test_config.py` expectations:
   - SQLite is accepted in development;
   - `mysql://` is rejected with a message naming the accepted schemes;
   - `APP_ENV=production` plus SQLite is rejected;
   - `database_url` defaults to `sqlite:///./beautybook.db`.
2. **Red** - add `tests/integration/test_sqlite_profile.py`:
   - pragmas (`foreign_keys`, `journal_mode`, `busy_timeout`);
   - foreign-key cascade through the ORM;
   - aware-UTC round trip;
   - `/ready` on SQLite;
   - duplicate email returns `409`, and register/login/`/auth/me` return `201/200/200`.
3. Run the suite and confirm the failures are the intended ones (validator, naive datetime,
   `TRUNCATE`, `diag` attribute).
4. **Green** - `app/core/config.py`: accepted schemes, production guard, development default.
5. **Green** - `app/infrastructure/database.py`: `build_engine` with SQLite pragmas and
   `UtcDateTime`.
6. **Green** - `app/modules/identity/models.py`: use `UtcDateTime` for every datetime column.
7. **Green** - `app/modules/identity/service.py`: dialect-neutral duplicate-email detection.
8. **Green** - `tests/conftest.py`: default SQLite test URL, shared engine builder, dialect-neutral
   cleanup instead of `TRUNCATE`.
9. **Refactor** - remove duplicated engine creation; keep one code path for pragmas.
10. **Verify** - full suite on SQLite, then again with `TEST_DATABASE_URL` pointing at PostgreSQL;
    migrations and `alembic check`; lint, format, mypy; live register/login check.

## 4. Database and migration plan

- No new migration. `0001` emits portable DDL (`Uuid`, `String`, `CHAR`, `DateTime`,
  `CURRENT_TIMESTAMP`, check and unique constraints).
- SQLite schema is created by `alembic upgrade head` against the file URL.
- PostgreSQL downgrade/upgrade cycle stays part of the fixture when that profile is selected.
- Rollback: delete the local `*.db` files and set the PostgreSQL URLs again. No data migration is
  involved.

## 5. API and frontend plan

### API

Unchanged. No route, schema, status code, or error code changes.

### Frontend

Unchanged. The Vite proxy and API base path are unaffected.

## 6. Test plan

- Unit: configuration matrix (SQLite, PostgreSQL, unsupported scheme, production guard, defaults).
- Integration on SQLite: pragmas, FK cascade, UTC round-trip, readiness, duplicate email,
  register/login/me.
- Integration on PostgreSQL: the existing suite with `TEST_DATABASE_URL`, including the registration
  race test.
- Migration: upgrade from empty on SQLite; `alembic check` on both backends.
- Manual: `uvicorn` from `backend/`, register and sign in through the browser or HTTP, confirm the
  database file path.

## 7. Observability and operations

- `/ready` keeps answering with `SELECT 1`, which is valid on both backends.
- Local file location is documented so it can be opened in DBeaver.
- WAL sidecar files are added to `.gitignore`.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Naive datetimes from SQLite break session expiry | `UtcDateTime` type; explicit round-trip test |
| Foreign keys silently off | `PRAGMA foreign_keys=ON` per connection; cascade test |
| Duplicate email becomes a 500 | Dialect-neutral detector; explicit 409 test on SQLite |
| Concurrent writes raise "database is locked" | WAL plus `busy_timeout`; concurrency evidence stays on PostgreSQL |
| Alembic reports type drift after the custom type | Verify with `alembic check` on both backends |
| Someone deploys SQLite to production | Validation error when `APP_ENV=production` |
| Local `.db` or WAL files committed | `.gitignore` patterns plus a `git status` check |

## 9. Rollout and rollback

Rollout: documentation and `.env` change only; no deployment. Rollback: point the two URLs back at
PostgreSQL and delete the local files. The code keeps supporting both, so rollback needs no revert.

## 10. Documentation updates

- `docs/adr/0011-sqlite-development-default.md` (new, supersedes ADR-0002 in part).
- `README.md`: stack table, key design decision, getting-started database section.
- `docs/ARCHITECTURE.md`: database policy and SQLite constraints.
- `AGENTS.md`: Section 12 amendment for the development default.
- `Task-List.md`: F-020 row and change-log entry.

## 11. Completion checklist

- [x] Tests written first and observed failing for the intended reasons
      (validator, naive datetime, `TRUNCATE`, `psycopg`-only `diag`)
- [x] Configuration accepts SQLite and PostgreSQL, rejects the rest, refuses SQLite in production
- [x] Engine pragmas verified
- [x] Aware-UTC round trip verified on both backends
- [x] Duplicate email still returns 409 on SQLite
- [x] Full suite green on SQLite
- [x] Full suite green on PostgreSQL, including the race test
- [x] `alembic upgrade head` and `alembic check` verified
- [x] lint, format, mypy clean
- [x] Live register and login verified
- [x] ADR, README, ARCHITECTURE, AGENTS, Task-List updated

## 12. Completion report

### What changed

- `app/core/config.py`: accepts `sqlite://` and `postgresql+psycopg://`, rejects other schemes,
  refuses SQLite when `APP_ENV=production`, defaults `database_url` to `sqlite:///./beautybook.db`,
  and treats an empty `TEST_DATABASE_URL=` in `.env` as unset.
- `app/infrastructure/database.py`: one `build_engine(database_url, poolclass=...)` used by the
  application, the tests, and Alembic; SQLite pragmas (`foreign_keys=ON`, `journal_mode=WAL`,
  `busy_timeout=5000`, `synchronous=NORMAL`) and `check_same_thread=False`; a `UtcDateTime` type
  that rejects naive binds and always reads back aware UTC.
- `app/modules/identity/models.py`: all nine datetime columns use `UtcDateTime()`.
- `app/modules/identity/service.py`: duplicate-email detection reads the constraint name first and
  falls back to the SQLite message, so both backends return `409 EMAIL_ALREADY_REGISTERED`.
- `migrations/env.py`: migrations run through `build_engine`, so a freshly migrated SQLite file is
  created in WAL mode with the same settings as the runtime.
- `tests/conftest.py`: SQLite test default, dialect-neutral cleanup, shared engine builder, and the
  "test database must differ from the development database" guard now only applies outside
  `APP_ENV=test` (CI legitimately points both URLs at the same test database).
- `tests/concurrency/test_registration_race.py`: refuses to run on non-PostgreSQL with an explicit
  reason instead of implying a SQLite concurrency guarantee.
- `.env`, `.env.example`, `.gitignore` (WAL sidecars), `.github/workflows/ci.yml` (a SQLite job
  that also runs `alembic upgrade head`/`check`, plus the renamed PostgreSQL job).

### Commands actually run

| Command | Result |
|---|---|
| `pytest -q` (SQLite default) | 269 passed, 1 skipped (concurrency needs PostgreSQL), 3.3 s |
| `TEST_DATABASE_URL=postgresql+psycopg://...:5433` + `pytest -q` | 269 passed, 1 skipped (`test_default_profile_is_sqlite`), 8.3 s |
| race test alone, PostgreSQL profile | 1 passed |
| race test alone, SQLite profile | 1 skipped, reason printed |
| `alembic upgrade head` (SQLite, file deleted first) | created `backend/beautybook.db`, 69 632 bytes, tables + revision `0001`, `journal_mode=wal` |
| `alembic check` (SQLite) | No new upgrade operations detected |
| `alembic upgrade head` + `alembic check` (PostgreSQL 5433) | applied, no drift |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 52 files already formatted |
| `mypy` | Success: no issues found in 23 source files |
| live `uvicorn` on 8123 + real HTTP register/login/`/auth/me` | `/ready` 200, register 201, login 200, me 200; row stored in `backend/beautybook.db` |

### Not run

- CI itself was not executed (the workflow file is updated; the jobs were reproduced locally).
- No frontend test run: no frontend file changed.

### Known limitations

- Concurrency is proven only on PostgreSQL. On SQLite the race test skips by design, and SQLite has
  a single writer, so `database is locked` remains possible under sustained write load.
- SQLite stores timestamps without a timezone; correctness depends on `UtcDateTime`. A future
  datetime column that forgets the type will silently reintroduce naive/aware comparison bugs.
- Future migrations that alter columns must use Alembic batch mode on SQLite.
- The local database file contains password and session hashes in plaintext and must never be
  committed or shared.

### Follow-up

- F-009 must record the PostgreSQL overlap-enforcement mechanism and must not claim SQLite
  equivalence.
- Choose a consolidated SRS before editing requirements again (see `SR-01` in the root `SRS.md`).
