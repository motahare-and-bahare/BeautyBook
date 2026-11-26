# F-020 Plan: SQLite Support

## Tests first (Red)

1. `tests/unit/test_config.py`: SQLite URLs are accepted, unsupported schemes are still rejected.
2. `tests/unit/test_duplicate_email_error.py`: psycopg constraint name and SQLite message are
   both recognized.
3. `tests/integration/test_sqlite_support.py`: migrate a temporary SQLite file, run
   `create-admin` through the CLI, log in, resolve the session, prove foreign keys are enforced,
   and paginate the admin list.

## Implementation (Green)

1. `app/core/config.py`: accept `sqlite+pysqlite://` and `sqlite://` alongside
   `postgresql+psycopg://`; keep rejecting everything else.
2. `app/infrastructure/database.py`:
   - `UTCDateTime` type decorator: write UTC, read naive values back as UTC.
   - `create_database_engine(url)`: `check_same_thread=False` and `PRAGMA foreign_keys=ON` for
     SQLite; the application and tests both use it.
3. `app/modules/identity/models.py`: use `UTCDateTime` for every timestamp. No schema change, so
   migration `0001` stays as released.
4. `app/modules/identity/service.py`: fall back to the SQLite message when psycopg's constraint
   diagnostics are absent.
5. `migrations/env.py`: `render_as_batch` for SQLite in online and offline mode.
6. `tests/conftest.py`: build the test engine with `create_database_engine`; clean tables with
   `DELETE` in child-first order.

## Documentation

- `docs/adr/0011-sqlite-support.md`, ADR index, and a superseded-in-part note on ADR-0002.
- `docs/features/F-020-sqlite-support/` (this SPEC and PLAN).
- `backend/README.md`: SQLite setup, migrations, `create-admin`, and the credential script.
- `.env.example`: commented SQLite alternative.
- `docs/ARCHITECTURE.md`, `AGENTS.md`, and `Task-List.md`: state the supported scope honestly.

## Risks and mitigations

- **Naive timestamps on SQLite** could compare incorrectly with aware values. Mitigated by
  `UTCDateTime` and asserted in the SQLite integration test.
- **No foreign-key enforcement** by default. Mitigated by the per-connection pragma and a test.
- **Threaded requests** could fail with `ProgrammingError`. Mitigated by
  `check_same_thread=False`.
- **SQLite is not production-equivalent for booking.** Documented in the ADR; concurrency tests
  stay on PostgreSQL.

## Rollback

No schema change. Reverting the configuration, engine, model type, and docs restores the
PostgreSQL-only behavior; an existing SQLite file still opens with any SQLite client.

## Completion checklist

- [x] Focused SQLite and unit tests pass (23 tests).
- [x] PostgreSQL suite passes (322 tests).
- [x] Ruff, format, and mypy are clean.
- [x] Documentation and change log updated.
