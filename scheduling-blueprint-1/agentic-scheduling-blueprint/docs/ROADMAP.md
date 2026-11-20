# Delivery Roadmap

This roadmap proposes an incremental path from an empty repository to a production-ready first release. It is a sequencing recommendation, not authorization to skip feature SPEC/PLAN approval.

## Phase 0 — Engineering foundation

**Tasks:** F-001  
**Outcome:** reproducible development environment and quality gates.

- Repository layout, frontend/backend bootstraps.
- Formatting, linting, type checking, test runners.
- CI pipeline.
- Environment configuration and secret handling.
- SQLite local configuration and PostgreSQL service for integration tests.
- Alembic baseline and health endpoints.
- Initial ADRs.

**Exit gate:** clean clone can run frontend/backend and all baseline checks in documented steps.

## Phase 1 — Identity and access control

**Tasks:** F-002, F-003  
**Outcome:** secure accounts and role boundaries.

- Registration, email verification, login/logout, password reset.
- User profile basics.
- Roles and permission model.
- Object-level authorization tests.

**Exit gate:** role and ownership tests prove users cannot access other users' or providers' resources.

## Phase 2 — Provider publishing

**Tasks:** F-004, F-005  
**Outcome:** providers can publish bookable services.

- Provider application/profile and public slug.
- Admin approval workflow if required.
- Service catalog with duration, price/currency, buffers, active state.
- Public profile and service pages.

**Exit gate:** only eligible/published providers and active services are public.

## Phase 3 — Availability engine

**Tasks:** F-006  
**Outcome:** correct provider availability.

- Weekly local-time rules.
- Date exceptions and time off.
- Timezone conversion and DST policy.
- Minimum notice, booking horizon, slot interval.
- Availability calculation unit tests and API tests.

**Exit gate:** boundary and DST tests pass; provider can preview availability accurately.

## Phase 4 — Booking core

**Tasks:** F-008  
**Outcome:** safe transactional booking.

- Booking state machine.
- Idempotency.
- Transactional slot revalidation.
- PostgreSQL overlap prevention mechanism.
- Service/policy/price snapshots.
- Concurrency integration tests against PostgreSQL.

**Exit gate:** simultaneous conflicting requests cannot create overlapping active bookings; retry does not duplicate.

## Phase 5 — Customer and provider workflows

**Tasks:** F-007, F-009, F-010, F-011  
**Outcome:** usable end-to-end scheduling product.

- Discovery and search.
- Customer booking list/detail.
- Provider calendar/list and booking management.
- Cancellation/rescheduling policies.
- Responsive accessible UX.

**Exit gate:** customer and provider Playwright journeys pass.

## Phase 6 — Notifications and administration

**Tasks:** F-012, F-013  
**Outcome:** operational platform controls and communication.

- Email verification and booking lifecycle email.
- Outbox/worker and reminder scheduler.
- Admin user/provider/booking management.
- Platform settings, audit log, basic operational metrics.

**Exit gate:** notification failures are retryable and do not corrupt bookings; privileged actions are audited.

## Phase 7 — Optional business integrations

**Tasks:** F-014, F-015, F-016  
**Outcome:** payments, external calendars, reporting if approved.

Each integration requires a dedicated SPEC, PLAN, threat review, adapter contract, and ADR. Do not couple core booking correctness to an external vendor's availability.

## Phase 8 — Production readiness

**Tasks:** F-017  
**Outcome:** deployable and supportable service.

- Security review and dependency scanning.
- Load/performance testing.
- PostgreSQL migration validation.
- Backup and restore exercise.
- Monitoring, alerting, incident and rollback runbooks.
- Privacy, terms, retention, and operational review.

**Release gate:** all P0 tasks Done, no unresolved critical security/data-integrity issues, restore test successful, and product decisions resolved.
