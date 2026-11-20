# ADR-0003: Booking Overlap Prevention Strategy

- **Status:** Proposed - must be finalized before F-009 implementation
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

Two customers may attempt to reserve overlapping times at the same salon. A read-then-insert
check in application code is unsafe: both requests can read "free" before either inserts, and both
can commit. The result is a double booking, which breaks the product's core promise.

The first release assumes capacity one per salon. Buffers also occupy time and must participate in
overlap prevention.

## Decision

Use a **PostgreSQL exclusion constraint** over the salon and the occupied interval:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE bookings
ADD CONSTRAINT bookings_no_overlap
EXCLUDE USING gist (
  salon_id WITH =,
  tstzrange(blocked_from, blocked_until, '[)') WITH &&
)
WHERE (status IN ('pending_confirmation', 'confirmed'));
```

Supporting rules:

- `blocked_from` and `blocked_until` include service buffers.
- Intervals are half-open `[start, end)`, so touching appointments do not conflict.
- Only slot-blocking states participate in the constraint.
- Booking creation happens in one transaction that revalidates availability.
- An idempotency key prevents duplicate bookings from retries.
- A constraint violation maps to `409 SLOT_UNAVAILABLE`.

The exact status representation and partial predicate must be confirmed in F-009.

## Alternatives considered

1. **Application-only overlap query.** Rejected: not safe under concurrency without additional
   locking, and easy to get wrong.
2. **Row lock on the salon row.** Viable, but serializes all bookings for a salon and requires
   careful proof. It may be kept as a supplementary measure, not the sole guarantee.
3. **Advisory locks.** Rejected as the primary mechanism: harder to reason about, tied to
   connection/session behavior, and less visible in the schema.
4. **Serializable isolation everywhere.** Rejected: higher retry complexity and performance cost;
   an explicit constraint expresses the invariant directly.

## Consequences

Positive:

- The invariant is enforced by the database, not by hope.
- Concurrent tests can prove correctness.
- The rule is visible in the schema.

Negative and risks:

- PostgreSQL is required for authoritative tests.
- The constraint must be maintained if blocking states change.
- Buffers must be computed correctly before insert.
- Future multi-staff capacity requires a different key (for example, staff/resource id), which
  needs a new ADR.

## Verification

Before F-009 is Done:

- A pytest concurrency test opens two transactions and attempts overlapping inserts.
- Exactly one commits; the other receives a conflict.
- Adjacent intervals both succeed.
- Buffer-inclusive overlaps are rejected.
- The same idempotency key returns the original booking rather than inserting twice.

SQLite results cannot satisfy this verification.

## References

- `docs/ARCHITECTURE.md`, Sections 11.5-11.7.
- `docs/SRS.md`, FR-BKG-006 to FR-BKG-008.
- `AGENTS.md`, Section 10.
