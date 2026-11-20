# ADR-0002: PostgreSQL as the Main Database, SQLite Only for Lightweight Tests

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook depends on database-level correctness for booking:

- overlapping interval prevention,
- transactions under concurrent requests,
- reliable unique constraints and indexes,
- predictable timezone-aware timestamp behavior.

A local database that behaves differently from production creates a dangerous gap: tests pass,
but production double-books or mishandles time.

## Decision

- **PostgreSQL** is the main application database for local development, integration tests, and
  production.
- **SQLite** is allowed only for fast, portable, unit-level tests that do not rely on
  PostgreSQL-specific behavior.
- SQLite is never used in production.
- Alembic manages all schema changes.
- PostgreSQL-specific features (such as `btree_gist` and exclusion constraints) live in migrations
  and are documented.

## Alternatives considered

1. **SQLite for local development and PostgreSQL in production.** Rejected: convenient, but tempts
   the team to rely on behavior that does not match production. It also makes concurrency testing
   an afterthought.
2. **SQLite everywhere.** Rejected: it cannot provide the required concurrency and exclusion
   constraint guarantees.
3. **A different relational database.** Rejected: PostgreSQL is mature, well documented, and
   supports the interval exclusion constraint needed for booking.

## Consequences

Positive:

- Local behavior matches production closely.
- Concurrency and constraint behavior can be tested honestly.
- One migration path for all environments.

Negative and risks:

- Local setup requires PostgreSQL (for example, Docker Compose).
- CI needs a PostgreSQL service.
- Some tests will be slower than an in-memory SQLite suite.

Follow-up:

- F-001 provides a documented local PostgreSQL setup.
- CI runs PostgreSQL integration and concurrency tests.
- Tests that use SQLite must state why SQLite is sufficient.

## References

- `docs/ARCHITECTURE.md`, Sections 11-12.
- `AGENTS.md`, Sections 5 and 12.
