# ADR-0003: Booking Overlap Prevention Strategy

- **Status:** Proposed — must be finalized before F-008 implementation
- **Date:** 2026-11-16

## Context

Two or more customers may attempt to reserve overlapping times for the same capacity-one provider. A read-then-insert check in application code is unsafe under concurrency.

## Decision

The preferred PostgreSQL design is a database exclusion constraint over provider/resource identity and a half-open `tstzrange(start_at, end_at, '[)')`, restricted to slot-blocking states. Use `btree_gist` if required. Buffers must be represented in the constrained occupied interval or enforced by an equivalent proven model. Booking creation also uses an explicit transaction and idempotency key.

If product requirements or schema constraints make this unsuitable, evaluate a provider/resource row-lock strategy and prove correctness with concurrent integration tests before accepting it.

## Consequences

- PostgreSQL is required for authoritative concurrency tests.
- SQLite tests remain useful for portable logic but cannot validate this invariant.
- Conflict errors must be mapped to a stable HTTP 409 response.
- The exact active-state predicate, hold expiry, and buffer representation must be specified in F-008.
