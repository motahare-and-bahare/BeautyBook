# Task List

This file is the project-wide intake and delivery control. Every feature must be registered here before implementation. A task is not Ready until its `SPEC.md` and `PLAN.md` exist and are reviewed.

## Status definitions

- `Proposed` — captured, not yet specified.
- `Specifying` — SPEC/PLAN are being prepared.
- `Review` — awaiting product/architecture approval.
- `Ready` — approved and eligible for implementation.
- `In Progress` — implementation underway using TDD.
- `Blocked` — waiting for a dependency or decision.
- `In Review` — implementation complete, awaiting review/verification.
- `Done` — Definition of Done satisfied.
- `Deferred` — intentionally postponed with rationale.

## Priority definitions

- `P0` — release blocker, security, or core data integrity.
- `P1` — required for first usable release.
- `P2` — valuable, can follow initial release.
- `P3` — optional enhancement.

## Feature intake checklist

For every new feature:
- [ ] Assign a unique ID (`F-###`).
- [ ] Add the task below with priority, dependencies, status, and links.
- [ ] Create `docs/features/F-###-short-name/SPEC.md`.
- [ ] Create `docs/features/F-###-short-name/PLAN.md`.
- [ ] Define customer/provider/admin journey as applicable.
- [ ] Add testable acceptance criteria and edge cases.
- [ ] Identify data, API, authorization, privacy, and operational impact.
- [ ] Create required ADR(s), or document why no ADR is needed.
- [ ] Review and approve before implementation.
- [ ] Implement Red → Green → Refactor.
- [ ] Update this list and the feature PLAN at completion.

## Initial project backlog

| ID | Feature / Workstream | Priority | Status | Dependencies | Specification | Plan |
|---|---|---:|---|---|---|---|
| F-001 | Repository foundation, tooling, CI, configuration | P0 | Proposed | — | `docs/features/F-001-foundation/SPEC.md` | `docs/features/F-001-foundation/PLAN.md` |
| F-002 | Identity, registration, login, sessions, password reset, email verification | P0 | Proposed | F-001 | `docs/features/F-002-identity/SPEC.md` | `docs/features/F-002-identity/PLAN.md` |
| F-003 | Role-based access control and provider/admin authorization | P0 | Proposed | F-002 | `docs/features/F-003-rbac/SPEC.md` | `docs/features/F-003-rbac/PLAN.md` |
| F-004 | Provider onboarding, profile, public profile page | P1 | Proposed | F-002, F-003 | `docs/features/F-004-provider-profile/SPEC.md` | `docs/features/F-004-provider-profile/PLAN.md` |
| F-005 | Service catalog, duration, price, currency, buffers | P1 | Proposed | F-004 | `docs/features/F-005-services/SPEC.md` | `docs/features/F-005-services/PLAN.md` |
| F-006 | Availability rules, weekly schedule, timezone, exceptions, time off | P0 | Proposed | F-004, F-005 | `docs/features/F-006-availability/SPEC.md` | `docs/features/F-006-availability/PLAN.md` |
| F-007 | Public discovery, search, filters, provider/service details | P1 | Proposed | F-004, F-005 | `docs/features/F-007-discovery/SPEC.md` | `docs/features/F-007-discovery/PLAN.md` |
| F-008 | Booking lifecycle, conflict prevention, idempotency | P0 | Proposed | F-002, F-005, F-006 | `docs/features/F-008-booking/SPEC.md` | `docs/features/F-008-booking/PLAN.md` |
| F-009 | Customer booking management and history | P1 | Proposed | F-008 | `docs/features/F-009-customer-bookings/SPEC.md` | `docs/features/F-009-customer-bookings/PLAN.md` |
| F-010 | Provider calendar and booking management | P1 | Proposed | F-008 | `docs/features/F-010-provider-bookings/SPEC.md` | `docs/features/F-010-provider-bookings/PLAN.md` |
| F-011 | Cancellation, rescheduling, policy enforcement | P1 | Proposed | F-008, F-009, F-010 | `docs/features/F-011-change-cancel/SPEC.md` | `docs/features/F-011-change-cancel/PLAN.md` |
| F-012 | Email notifications and scheduled reminders | P1 | Proposed | F-008 | `docs/features/F-012-notifications/SPEC.md` | `docs/features/F-012-notifications/PLAN.md` |
| F-013 | Platform administration, moderation, configuration, audit | P1 | Proposed | F-002, F-003 | `docs/features/F-013-admin/SPEC.md` | `docs/features/F-013-admin/PLAN.md` |
| F-014 | Payment collection, refunds, payment webhooks | P2 | Proposed | F-008, F-012 | `docs/features/F-014-payments/SPEC.md` | `docs/features/F-014-payments/PLAN.md` |
| F-015 | External calendar integration and synchronization | P2 | Proposed | F-006, F-008, F-012 | `docs/features/F-015-calendar-sync/SPEC.md` | `docs/features/F-015-calendar-sync/PLAN.md` |
| F-016 | Reporting, operational dashboards, exports | P2 | Proposed | F-008, F-013 | `docs/features/F-016-reporting/SPEC.md` | `docs/features/F-016-reporting/PLAN.md` |
| F-017 | Production hardening, backup/restore, observability, security review | P0 | Proposed | F-001–F-013 | `docs/features/F-017-production-readiness/SPEC.md` | `docs/features/F-017-production-readiness/PLAN.md` |

## Current sprint

No sprint has been committed yet. Select work only from tasks whose status is `Ready`.

## Change log

| Date | Change |
|---|---|
| 2026-11-16 | Initial backlog and feature-intake workflow created. |
