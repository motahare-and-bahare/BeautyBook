# ADR-0002: SQLite for Local Development, PostgreSQL for Production

- **Status:** Accepted
- **Date:** 2026-11-16

## Context

Fast local setup is desirable, while production needs robust transactional behavior and database-level concurrency guarantees for booking.

## Decision

Use SQLAlchemy 2.x and Alembic. SQLite is the default local development database and may be used for fast portable tests. PostgreSQL is mandatory in production and for authoritative integration, migration, and concurrency tests.

## Consequences

- Application logic should remain portable where practical.
- PostgreSQL-specific constraints and SQL must be isolated and documented.
- CI must run a PostgreSQL test job.
- SQLite results alone cannot establish booking concurrency correctness.
