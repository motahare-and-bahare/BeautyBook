# Task List

**Project:** BeautyBook - Online Salon Marketplace
**Last updated:** 2026-11-19

This file is the single delivery queue for the project. Every feature must be registered here
before implementation. A task is not Ready until its `SPEC.md` and `PLAN.md` exist and have been
reviewed.

> The specification and plan paths below are **reserved locations**. They are created during
> feature intake, not pre-filled with empty placeholders. This follows the rule that a feature
> document must contain real, reviewed content.

---

## 1. Status definitions

| Status | Meaning |
|---|---|
| `Proposed` | Captured, not yet specified. |
| `Specifying` | `SPEC.md` and `PLAN.md` are being written. |
| `Review` | Awaiting product/architecture approval. |
| `Ready` | Approved and eligible for implementation. |
| `In Progress` | Implementation underway using TDD. |
| `Blocked` | Waiting on a dependency or decision. |
| `In Review` | Implementation complete, awaiting verification/review. |
| `Done` | Definition of Done satisfied. |
| `Deferred` | Intentionally postponed, with a recorded reason. |

## 2. Priority definitions

| Priority | Meaning |
|---|---|
| `P0` | Release blocker, security issue, or core data-integrity requirement. |
| `P1` | Required for the first usable release. |
| `P2` | Valuable, can follow the first release. |
| `P3` | Optional enhancement. |

## 3. Feature intake checklist

For every new feature:

- [ ] Assign a unique ID (`F-###`).
- [ ] Add a row to the backlog table with priority, status, dependencies, and document links.
- [ ] Create `docs/features/F-###-short-name/SPEC.md`.
- [ ] Create `docs/features/F-###-short-name/PLAN.md`.
- [ ] Describe the customer, salon owner, and/or administrator journey as applicable.
- [ ] Add testable acceptance criteria and edge cases.
- [ ] Identify data, API, authorization, privacy, and operational impact.
- [ ] Create the required ADR(s), or document why no ADR is needed.
- [ ] Review and approve the SPEC/PLAN before implementation.
- [ ] Implement using Red -> Green -> Refactor.
- [ ] Run tests and verification commands; record the actual results.
- [ ] Update this list, the feature PLAN, and affected documentation.
- [ ] Mark `Done` only after verification.

---

## 4. Backlog

| ID | Feature / Workstream | Module | Priority | Status | Depends on | SPEC | PLAN |
|---|---|---|---:|---|---|---|---|
| F-000 | Initial documentation and repository skeleton | project | P0 | Done | - | `AGENTS.md`, `docs/` | - |
| F-001 | Authentication and registration gate: customer signup, salon-owner application, admin approval, roles, protected routes, minimal app foundation | identity | P0 | In Progress | F-000 | `docs/features/F-001-authentication/SPEC.md` | `docs/features/F-001-authentication/PLAN.md` |
| F-002 | Authorization and ownership policies: role permissions and resource-level access checks | identity | P0 | Proposed | F-001 | `docs/features/F-002-authorization/SPEC.md` | `docs/features/F-002-authorization/PLAN.md` |
| F-003 | Account lifecycle and profile: email verification, password reset, profile, auth rate limiting | identity | P1 | Proposed | F-001 | `docs/features/F-003-account-lifecycle/SPEC.md` | `docs/features/F-003-account-lifecycle/PLAN.md` |
| F-004 | Salon profile: onboarding, public salon page, address, contact, publishing | salons | P1 | Proposed | F-002, F-003 | `docs/features/F-004-salon-profile/SPEC.md` | `docs/features/F-004-salon-profile/PLAN.md` |
| F-005 | Services and pricing: CRUD, duration, price, currency, buffers, activation | services | P1 | Proposed | F-004 | `docs/features/F-005-services/SPEC.md` | `docs/features/F-005-services/PLAN.md` |
| F-006 | Portfolio and images: secure upload, ordering, cover photo, deletion | portfolio | P1 | Proposed | F-004 | `docs/features/F-006-portfolio/SPEC.md` | `docs/features/F-006-portfolio/PLAN.md` |
| F-007 | Working hours, availability, and time off | availability | P0 | Proposed | F-004, F-005 | `docs/features/F-007-availability/SPEC.md` | `docs/features/F-007-availability/PLAN.md` |
| F-008 | Public discovery: search, filters, salon comparison, service comparison | salons | P1 | Proposed | F-004, F-005 | `docs/features/F-008-discovery/SPEC.md` | `docs/features/F-008-discovery/PLAN.md` |
| F-009 | Appointment booking: state machine, conflict prevention, idempotency | bookings | P0 | Proposed | F-002, F-005, F-007 | `docs/features/F-009-booking/SPEC.md` | `docs/features/F-009-booking/PLAN.md` |
| F-010 | Customer dashboard: upcoming/past bookings, details, cancel, reschedule | bookings | P1 | Proposed | F-009 | `docs/features/F-010-customer-bookings/SPEC.md` | `docs/features/F-010-customer-bookings/PLAN.md` |
| F-011 | Salon owner dashboard: appointment list/calendar and booking management | bookings | P1 | Proposed | F-009 | `docs/features/F-011-owner-bookings/SPEC.md` | `docs/features/F-011-owner-bookings/PLAN.md` |
| F-012 | Cancellation and rescheduling policies with audit history | bookings | P1 | Proposed | F-009, F-010, F-011 | `docs/features/F-012-cancellation-policies/SPEC.md` | `docs/features/F-012-cancellation-policies/PLAN.md` |
| F-013 | Email notifications and reminders using an outbox | notifications | P1 | Proposed | F-009 | `docs/features/F-013-notifications/SPEC.md` | `docs/features/F-013-notifications/PLAN.md` |
| F-014 | Administration: users, salon moderation, settings, audit log, support actions | administration | P1 | Proposed | F-002, F-003, F-004 | `docs/features/F-014-administration/SPEC.md` | `docs/features/F-014-administration/PLAN.md` |
| F-015 | Customer reviews and ratings | reviews | P2 | Deferred | F-009, F-012 | `docs/features/F-015-reviews/SPEC.md` | `docs/features/F-015-reviews/PLAN.md` |
| F-016 | Deposits, online payments, refunds | payments | P2 | Deferred | F-009, F-012, F-013 | `docs/features/F-016-payments/SPEC.md` | `docs/features/F-016-payments/PLAN.md` |
| F-017 | Reporting and operational dashboards | reporting | P2 | Deferred | F-009, F-014 | `docs/features/F-017-reporting/SPEC.md` | `docs/features/F-017-reporting/PLAN.md` |
| F-018 | Production readiness: security review, backups, observability, runbooks | platform | P0 | Proposed | F-001 - F-014 | `docs/features/F-018-production-readiness/SPEC.md` | `docs/features/F-018-production-readiness/PLAN.md` |
| F-019 | Persian localization and RTL layout for the login and customer-registration screens (copy, `dir="rtl"`, Persian font stack) | frontend | P1 | Done | F-001 | `docs/features/F-019-persian-rtl-auth/SPEC.md` | `docs/features/F-019-persian-rtl-auth/PLAN.md` |

### Notes on task IDs

- `F-000` is a **project chore**, not a product feature. It is recorded here for traceability and
  is already complete.
- `F-001` is a **vertical slice**: it includes the minimum application foundation needed to run,
  test, and protect authentication (project bootstrap, PostgreSQL connection, Alembic baseline,
  test harness, health check).
- `F-001` also owns the **registration gate**:
  - `/register` creates an active **customer** account.
  - `/register/owner` creates a **pending** account plus a pending salon application. No session is
    created and the `salon_owner` role is not granted until an administrator approves it.
  - the administrator role is never available through public registration; the first administrator
    is provisioned by a local CLI command and later administrators are granted by an existing
    administrator.
  - a minimal admin review endpoint and page are included so the approval gate is testable and
    usable end to end.
- `F-001` does **not** include the full salon profile, services, images, availability, booking,
  the owner dashboard, or full administration. Those are F-004 onward.
- `F-001` does not include email verification, password reset, profile editing, or authentication
  rate limiting; those are F-003.
- `F-015` (reviews), `F-016` (payments), and `F-017` (reporting) are deliberately deferred. They
  must not be implemented before the core booking journey is stable and their product decisions
  are resolved.
- `F-018` is a P0 release gate even though it is sequenced last. Production readiness is not
  optional, but it depends on the features it must verify.

---

## 5. Current sprint

**Sprint 0 - Documentation baseline: complete.**

Deliverables:

- `AGENTS.md`, `Task-List.md`, `README.md`.
- `docs/ARCHITECTURE.md`, `docs/SRS.md`, `docs/ROADMAP.md`.
- Initial ADRs `0001`-`0010`.
- Documentation templates.
- Empty, documented repository skeleton for backend, frontend, infrastructure, and CI.

**Sprint 1 - Authentication and registration gate (`F-001`): in progress.**

- SPEC: `docs/features/F-001-authentication/SPEC.md`
- PLAN: `docs/features/F-001-authentication/PLAN.md`
- Status: `In Progress`; Steps 0-5, Step 7, Step 8, and the customer registration/login frontend
  slice are implemented and verified. Owner application, administrator review, logout, the account
  dashboard, and the remaining screens remain.
- Scope change (2026-11-18): separate customer and salon-owner registration flows; salon-owner
  accounts and applications require administrator approval; administrator accounts are never public.
- Approved decisions: ADR-0005 (session strategy) and ADR-0010 (registration flows and role
  assignment) are `Accepted`.
- Implementation follows the 16-step TDD order in `PLAN.md`.

---

## 6. Dependency graph (high level)

```text
F-000 (docs)
  |
  v
F-001 (authentication + minimal foundation)
  |                              |
  v                              v
F-002 (authorization)        F-003 (account lifecycle)
  \                              /
   +------------+---------------+
                v
         F-004 (salon profile)
          /              \
         v                v
   F-005 (services)   F-006 (portfolio)
         |                |
         +-------+--------+
                 v
           F-007 (availability)
                 |
                 v
           F-009 (booking core)
            /            \
           v              v
    F-010 (customer)  F-011 (owner)
            \            /
             v          v
       F-012 (cancellation/reschedule)
                 |
                 v
         F-013 (notifications)

F-008 (discovery) can proceed after F-004/F-005.
F-014 (admin) can proceed after F-002/F-003/F-004.
F-015/F-016/F-017 are deferred until after the first usable release.
F-018 verifies everything before launch.
```

`F-001` delivers the approval gate (pending owner -> administrator decision -> dashboard access).
`F-004` builds the full salon profile after an owner is approved; it does not decide whether an
owner may exist.

---

## 7. Change log

| Date | Change |
|---|---|
| 2026-11-18 | Initial BeautyBook documentation baseline created; F-000 marked Done and F-001-F-018 registered. |
| 2026-11-18 | F-001 re-scoped to the authentication vertical slice; F-002 now authorization/ownership and F-003 account lifecycle/profile. F-001 SPEC/PLAN created and moved to Review. |
| 2026-11-18 | Product decision: separate customer and salon-owner registration flows. Owner accounts and salon applications require administrator approval. Admin accounts are never public. F-001 SPEC/PLAN, ADR-0010, architecture, SRS, roadmap, and README revised; no code written. |
| 2026-11-18 | Project owner approved the revised design. ADR-0005 and ADR-0010 accepted; F-001 moved from `Review` to `Ready`. No application code written yet. |
| 2026-11-18 | F-001 moved to `In Progress`. Step 0 implemented with TDD: backend foundation (config, request IDs, error envelope, lazy database engine, health/readiness, CLI boundary), frontend shell (Vite, router, Pinia, tokens), `.env.example`, Compose file, and CI. Backend 18 tests, frontend 2 tests, lint/typecheck/build pass. |
| 2026-11-18 | F-001 Step 1 implemented with TDD: framework-free identity domain rules (email normalization, password policy, roles, user-status and owner-application transitions, IANA timezone and ISO 4217 currency validation, safe redirect). 124 unit and 4 integration backend tests pass; lint, format, and mypy clean. |
| 2026-11-18 | F-001 Step 2 implemented with TDD: SQLAlchemy models for `users`, `user_roles`, `sessions`, and `owner_applications`; Alembic environment plus migration `0001_authentication` with unique/check/cascade constraints and indexes. Upgrade -> downgrade -> upgrade verified on PostgreSQL; `alembic check` reports no drift; 147 backend tests pass. |
| 2026-11-19 | F-001 Step 3 implemented with TDD: framework-free CSRF token generation and constant-time comparison, `require_csrf` dependency that rejects before any handler or database access, `GET /api/v1/auth/csrf` issuing a readable double-submit cookie, and cookie/header names moved into configuration. 162 backend tests pass; lint, format, mypy, and a live server check pass. |
| 2026-11-19 | F-001 Step 4 implemented with TDD: SHA-256 session-token hashing and opaque token generation, pure session-validity policy (expiry boundary, revocation, non-active account), identity repository for sessions and users, and session use cases with injectable clock/ttl/hasher. Migration `0001` applied to the development PostgreSQL database; 184 backend tests pass, lint/format/mypy clean, `/ready` reports the database healthy. |
| 2026-11-19 | F-001 Step 5 implemented with TDD: atomic customer registration (`POST /api/v1/auth/register/customer`) creating an active user, the `customer` role, and a session in one commit; Argon2id password hashing with configurable cost; safe user response; HttpOnly session and readable CSRF cookies; duplicate-email 409 mapping including concurrent races; schema rejects privileged fields. 218 backend tests pass, including PostgreSQL integration, atomic rollback, and two-request concurrency; lint/format/mypy clean; live-server registration smoke test passed against a disposable database. |
| 2026-11-19 | F-001 frontend authentication slice implemented with TDD: typed API client with cookie credentials, CSRF bootstrap/refresh/retry, and backend error-envelope mapping; customer registration page with client validation, duplicate-email state, and no role/admin choice; login page wired to the future `/auth/login` endpoint; shared accessible form/layout components; `/register` route. 17 frontend tests pass; typecheck and production build clean; browser-to-backend registration returned 201 with the `customer` role and active status. Login remains unavailable until the backend Step 7 endpoint is implemented. |
| 2026-11-19 | F-001 Step 7 implemented with TDD: `POST /api/v1/auth/login` verifies the Argon2id hash, uses a dummy hash for unknown emails, returns a generic `401 INVALID_CREDENTIALS`, reveals `ACCOUNT_PENDING_APPROVAL`/`ACCOUNT_REJECTED`/`ACCOUNT_SUSPENDED` only after a correct password, rehashes outdated hashes, rotates the caller's current session while keeping other sessions valid, and issues fresh session/CSRF cookies. The Vue login page now works against the live endpoint and shows the status-aware messages. 243 backend tests pass; 19 frontend tests pass; lint/format/mypy, typecheck, and production build clean; live browser check registered a customer, rejected a wrong password with 401, signed in with 200, and PostgreSQL showed 2 sessions with 1 revoked by rotation. |
| 2026-11-19 | F-001 Step 8 implemented with TDD: `GET /api/v1/auth/me` resolves the opaque session cookie, rejects missing/unknown/expired/revoked/non-active sessions with `401 UNAUTHENTICATED`, and returns the safe user shape with roles read from the database on every request. Added `CurrentUser` and the reusable `require_roles(...)` dependency, which validates role names at wiring time, permits any one matching role, and returns `403 FORBIDDEN` without calling the handler. 259 backend tests pass; lint, format, and mypy clean; README now documents the exact two-terminal run commands. |
| 2026-11-20 | F-019 implemented with TDD: the login and customer-registration screens are now Persian and right to left. `index.html` declares `lang="fa" dir="rtl"`; the font stack prefers Vazirmatn then Persian-capable system fonts; all headings, labels, hints, buttons, status/role labels and frontend error messages are Persian; backend field errors are mapped to Persian text; email and password inputs keep `dir="ltr"`. No dependency was added. 25 frontend tests pass; typecheck and production build clean; a live browser check confirmed `lang=fa`, `dir=rtl`, Persian validation and duplicate-email messages, and Persian success panels. |
