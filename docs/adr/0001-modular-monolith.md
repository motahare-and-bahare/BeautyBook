# ADR-0001: Start with a Modular Monolith

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook is an early-stage marketplace. Its core workflows need strongly consistent transactions
across salon services, availability, and bookings. The team is small and the project owner is
learning, so operational simplicity and clear code boundaries matter more than independent
deployment of services.

A booking operation must atomically check availability, reserve an interval, and record history.
Splitting that across network boundaries would add failure modes before the product has proven a
need for them.

## Decision

Build the backend as a **modular monolith**:

- one FastAPI application,
- one primary PostgreSQL database,
- explicit domain modules (`identity`, `salons`, `services`, `portfolio`, `availability`,
  `bookings`, `notifications`, `administration`),
- dependency direction from router to service to repository/domain,
- no cross-module imports of ORM models,
- no microservices, event sourcing, CQRS, or distributed locks in the initial releases.

## Alternatives considered

1. **Microservices from the start.** Rejected: too much operational and consistency complexity for
   an early-stage product; booking would require distributed transactions or sagas.
2. **Single-layer application without module boundaries.** Rejected: faster to start, but becomes
   a tangle as services, availability, and booking rules grow.
3. **Serverless functions per endpoint.** Rejected: harder local development and transaction
   management for this workload, with no demonstrated scaling need.

## Consequences

Positive:

- Simple deployment and debugging.
- Strong transactional consistency for booking.
- One codebase and one database to reason about.
- Module boundaries preserve a future extraction path.

Negative and risks:

- One deployment unit scales as a whole.
- Module boundaries can erode without review; dependency rules must be enforced by code review and
  tests.
- A future extraction will require real work, not just a deployment change.

Follow-up:

- Document module boundaries in `docs/ARCHITECTURE.md`.
- Reject cross-module ORM imports during review.
- Require a new ADR, supported by measurable need, before extracting a service.

## References

- `docs/ARCHITECTURE.md`, Sections 4-5.
- `AGENTS.md`, Section 6.
