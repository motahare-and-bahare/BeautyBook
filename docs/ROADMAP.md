# Delivery Roadmap

**Product:** BeautyBook - Online Salon Marketplace
**Version:** 1.0
**Date:** 2026-11-18

This roadmap sequences the work from the current documentation baseline to a production-ready
first release. It is a recommendation, not authorization to skip the feature intake gate. Each
phase ends with an exit gate that must be verified before the next phase starts.

Sizes are rough: **S** = a few focused sessions, **M** = a meaningful feature, **L** = the hardest
or largest work in the project.

---

## Phase 0 - Documentation baseline (complete)

**Tasks:** F-000
**Status:** Done
**Size:** S

**Outcome:** A shared understanding of the product, architecture, workflow, and decisions before
any code is written.

Delivered:

- `AGENTS.md` engineering rules.
- `Task-List.md` backlog and intake gate.
- `docs/SRS.md` requirements.
- `docs/ARCHITECTURE.md` design baseline.
- `docs/ROADMAP.md`.
- Initial ADRs 0001-0010.
- SPEC, PLAN, and ADR templates.
- Empty but documented backend, frontend, infrastructure, and CI skeleton.

**Exit gate:** The project owner has read the documents and approved the direction. No application
code exists yet.

---

## Phase 1 - Authentication vertical slice

**Tasks:** F-001
**Size:** L

**Outcome:** The first runnable application and a secure registration gate: customers can register
and sign in, salon owners can apply and wait for administrator approval, administrators can review
applications, and roles and protected routes are enforced.

Work:

- Create the minimal Python and Vue/Vite project configuration.
- Add formatting, linting, type checking, and test runners.
- Add local PostgreSQL setup (for example, Docker Compose).
- Add `.env.example` with placeholders only; `.env` stays out of Git.
- Add configuration loading and validation.
- Add FastAPI bootstrap, `/api/v1` router composition, health/readiness endpoints, and request IDs.
- Add SQLAlchemy engine/session setup and the initial Alembic migration.
- Add `users`, `user_roles`, `sessions`, and `owner_applications`.
- Add customer registration with auto-login.
- Add salon-owner application with a pending account and pending application; no session and no
  owner role until approval.
- Add administrator review: list, approve, reject with reason.
- Add the administrator bootstrap CLI and the administrator-only role grant.
- Add login with account-status handling, logout, `/auth/me`, and CSRF token issuance.
- Use Argon2id password hashing and HttpOnly cookie sessions.
- Add the role-checking dependency and frontend route guards.
- Add a minimal owner placeholder and a minimal admin review page.
- Add a minimal CI pipeline: install, lint, type check, test, migration check.
- Add run and administrator-bootstrap instructions to `README.md`.
- Write tests first: configuration, health, domain rules, models, CSRF, sessions, customer
  registration, owner application, login status codes, logout, `/auth/me`, role denial, CLI,
  approval concurrency, and duplicate-email concurrency.

**Exit gate:**

- A clean clone can start the backend and frontend using documented steps.
- Health and readiness checks respond correctly.
- A visitor can register as a customer, refresh the page, and log out.
- A visitor can apply as a salon owner, sees the pending notice, and cannot sign in.
- An administrator can approve the application; the owner can then sign in and reach `/owner`.
- A rejected owner cannot sign in.
- A protected API route returns `401` without a valid session.
- An administrator endpoint returns `403` for a customer and succeeds for an administrator.
- No public endpoint can create an administrator; the CLI creates the first one.
- Duplicate email returns `409`; concurrent duplicates produce exactly one account.
- Concurrent approvals produce exactly one success.
- CSRF is required and enforced on state-changing requests, including admin actions.
- Passwords are Argon2id hashes; no plaintext password, token, email, or phone appears in logs.
- Lint, format check, type check, backend tests, frontend tests, and migration upgrade/downgrade
  pass.
- CI runs the same checks.
- No secrets are committed.

**Why this phase matters (simple terms):** it builds the workbench and the front door at the same
time. After this phase, the project is a real application with real accounts, not just documents.

---

## Phase 2 - Authorization, account lifecycle, and auth hardening

**Tasks:** F-002, F-003
**Size:** L

**Outcome:** Complete account lifecycle and resource-level authorization for customers, salon
owners, and administrators.

Work:

- Resource-ownership policies for salons, services, photos, hours, and bookings.
- Negative authorization tests for every protected resource.
- Email verification tokens and flow.
- Password reset with short-lived single-use tokens.
- Password change, "sign out everywhere", and profile basics.
- Preferred timezone and notification preferences.
- Applying to become an owner from an existing customer account.
- Rate limiting and account lockout for authentication endpoints.
- Expired-session cleanup.
- Security review of cookies, CSRF, session rotation, and error responses.

**Exit gate:**

- A user can verify their email and reset a forgotten password.
- A customer cannot access owner or admin endpoints.
- An owner cannot access another owner's resources.
- A customer cannot access another customer's booking.
- Auth endpoints are rate-limited.
- Session and CSRF behavior is tested.
- No plaintext password or token appears in logs.
- The account lifecycle does not weaken the F-001 registration gate.

**Why this phase matters:** every later feature depends on knowing who the user is and exactly what
they are allowed to touch.

---

## Phase 3 - Salon publishing

**Tasks:** F-004, F-005, F-006
**Size:** L

**Outcome:** A salon owner can create a credible public salon page with services, prices, and
photos.

Work:

- Complete the salon profile for an already-approved owner; owner role activation happens in F-001.
- Salon profile fields: full address, unique slug, description, contact, timezone, currency.
- Publish/unpublish after the F-001 approval gate.
- Public salon page read model.
- Service CRUD with duration, price, buffers, active/archive state.
- Image upload with content validation, size limits, random storage keys, alt text, ordering, and
  cover photo.
- Storage adapter and metadata model.
- Authorization tests for every owner action.

**Exit gate:**

- An owner can create, edit, and publish a salon.
- Only published salons and active services are public.
- An owner cannot edit another salon or its services/images.
- Invalid and malicious uploads are rejected.
- Prices are stored as integer minor units with a currency.
- Historical booking snapshots are unaffected by service edits (design verified in tests where
  applicable).

**Why this phase matters:** a marketplace needs something worth browsing before it needs
availability or booking.

---

## Phase 4 - Working hours and availability

**Tasks:** F-007
**Size:** L

**Outcome:** Correct, timezone-aware availability that both customers and owners can trust.

Work:

- Weekly working hours with multiple intervals per day.
- Time off and unavailable periods.
- Slot generation with service duration, buffers, slot step, minimum notice, and booking horizon.
- IANA timezone conversion with `zoneinfo`.
- DST policy for nonexistent and ambiguous local times.
- Availability API with UTC and local display fields.
- Owner preview of availability.
- Validation of overlapping or invalid working hours.
- Unit tests for slot math and DST boundaries.

**Exit gate:**

- A closed day produces no slots.
- A split shift produces the correct two windows.
- Time off removes the correct slots.
- DST boundary tests pass.
- Availability respects duration, buffers, notice, and horizon.
- The API clearly states the timezone used.

**Why this phase matters:** almost every booking bug starts with a time calculation bug. This is
where the hard thinking happens before any reservation exists.

---

## Phase 5 - Public discovery

**Tasks:** F-008
**Size:** M

**Outcome:** Customers can find and compare salons without already knowing the name.

Work:

- Public salon list with pagination.
- Search by salon name and city.
- Search/filter by service and category.
- Price-range filtering.
- Availability-aware filtering if approved.
- Salon comparison and service comparison views.
- Empty, loading, and error states.
- Search indexes and query performance checks.

**Exit gate:**

- A customer can find a salon by name, city, and service.
- Filters combine correctly and paginate predictably.
- Unpublished/suspended salons never appear.
- Search queries are indexed and measured.
- Mobile layout is usable.

**Why this phase matters:** discovery is the front door of the marketplace.

---

## Phase 6 - Booking core

**Tasks:** F-009
**Size:** L (highest-risk phase)

**Outcome:** A trustworthy booking command that cannot double-book a salon.

Work:

- Booking state machine and legal transitions.
- Booking request and response schemas.
- Slot revalidation inside the transaction.
- Occupied interval including buffers.
- PostgreSQL exclusion constraint and `btree_gist` migration.
- Stable `409 SLOT_UNAVAILABLE` mapping.
- Idempotency key handling and request fingerprint.
- Service/price/timezone/policy snapshots.
- Booking event history.
- Transactional outbox message creation.
- Concurrency tests against PostgreSQL.
- Booking confirmation page and email trigger.

**Exit gate:**

- Two simultaneous overlapping requests create exactly one active booking.
- Adjacent bookings (`10:00-10:30` and `10:30-11:00`) both succeed.
- Buffers block the correct extra time.
- A retry with the same idempotency key returns the original booking.
- A different request with the same key is rejected.
- A booking that violates hours, time off, notice, or horizon is rejected.
- The concurrency suite runs against PostgreSQL, not SQLite.
- Notification failure cannot roll back a booking.

**Why this phase matters:** this is the core promise of the product. A marketplace that
double-books is not trustworthy.

---

## Phase 7 - Customer and owner workflows

**Tasks:** F-010, F-011, F-012
**Size:** L

**Outcome:** A usable end-to-end product after the booking is created.

Work:

- Customer dashboard: upcoming, past, cancelled, details, history.
- Owner dashboard: today/upcoming, filters, details, confirm/reject if approval mode applies.
- Cancellation with policy validation and reason.
- Rescheduling with transactional revalidation and history.
- Notifications for changes.
- Empty/loading/error states and accessible interactions.
- E2E journeys for customer and owner.

**Exit gate:**

- A customer can view and cancel their own booking.
- A customer cannot view another customer's booking.
- An owner can see and manage only their salon's bookings.
- Cancellation frees the slot.
- Rescheduling preserves history and cannot create an overlap.
- E2E tests pass for the core journeys.

---

## Phase 8 - Notifications and administration

**Tasks:** F-013, F-014
**Size:** L

**Outcome:** The platform can communicate reliably and be operated safely.

Work:

- Transactional outbox worker.
- Email templates for verification, reset, booking created/cancelled/rescheduled.
- Reminder scheduling and deduplication.
- Retry with bounded backoff and failure visibility.
- Admin user and salon management.
- Salon approval/suspension workflow.
- Platform settings and service categories.
- Audit log for privileged actions.
- Support booking search and controlled interventions.
- Basic operational metrics.

**Exit gate:**

- Email failures are retryable and do not corrupt bookings.
- Reminders are not duplicated.
- Every privileged action is audited with actor, target, reason, and timestamp.
- A suspended salon cannot receive new bookings.
- Admin actions are covered by negative authorization tests.

---

## Phase 9 - Deferred growth features

**Tasks:** F-015 (reviews), F-016 (payments), F-017 (reporting)
**Size:** M-L each
**Status:** Deferred

**Outcome:** Only if the business requirements justify them after the first usable release.

Each item needs its own SPEC, PLAN, threat review, and ADR before implementation:

- Reviews: completed-booking eligibility, one review per booking, moderation, aggregate rating.
- Payments: provider choice, deposits, refunds, webhook verification, reconciliation, PCI scope.
- Reporting: privacy-safe aggregates, exports, retention.

**Exit gate:** each feature meets its own acceptance criteria and does not weaken booking
correctness, privacy, or operational simplicity.

---

## Phase 10 - Production readiness

**Tasks:** F-018
**Size:** L

**Outcome:** A deployable, supportable, recoverable service.

Work:

- Security review and dependency scanning.
- Load and performance testing.
- PostgreSQL migration validation from the previous schema.
- Backup and restore exercise.
- Monitoring, alerting, and dashboards for critical flows.
- Incident, rollback, and migration runbooks.
- Privacy notice, terms, retention, and deletion procedures.
- Accessibility audit against WCAG 2.2 AA.
- Final end-to-end regression suite.

**Release gate:**

- All P0 tasks are Done.
- No unresolved critical/high security or data-integrity issue.
- Concurrency suite passes on PostgreSQL.
- Restore test succeeds.
- Migration upgrade and rollback are documented and rehearsed.
- Product decisions in `docs/SRS.md` Section 13 are resolved.
- The completion report is honest about remaining limitations.

---

## Milestone summary

| Milestone | Phases | What works |
|---|---|---|
| M0 - Blueprint | 0 | Documents and skeleton. |
| M1 - Accounts | 1 | App boots; customer signup, owner application and approval, login/logout, protected routes. |
| M2 - Trust | 2 | Ownership policies, email verification, password reset, rate limiting. |
| M3 - Storefront | 3 | Salons publish services and photos. |
| M4 - Schedule | 4 | Correct availability. |
| M5 - Discovery | 5 | Customers find and compare salons. |
| M6 - Booking | 6 | Safe, conflict-free booking. |
| M7 - Lifecycle | 7 | Customers and owners manage appointments. |
| M8 - Operations | 8 | Email and administration. |
| M9 - Launch | 10 | Production-ready release. |

---

## Recommended next task

**F-001 - Authentication and registration gate.** Status: `Ready`, approved 2026-11-18.

ADR-0005 (session strategy) and ADR-0010 (registration flows and role assignment) are accepted.
Implementation follows the 16-step TDD order in the PLAN, starting with the minimal application
foundation: configuration validation, health checks, and domain rules as failing tests first.

Do not begin F-002 until F-001's exit gate is verified.
