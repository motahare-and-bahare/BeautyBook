# Software Architecture Document (SAD)

**Product:** Multi-provider Online Scheduling Platform  
**Status:** Initial architecture baseline  
**Version:** 1.0  
**Date:** 2026-11-16

## 1. Purpose and scope

This document describes the logical and deployment architecture for an online scheduling platform. It establishes the technical baseline, key quality attributes, domain boundaries, persistence strategy, booking consistency model, and evolution rules.

The first release targets a single deployable product serving multiple independent service providers. The architecture deliberately starts as a modular monolith. Microservices are not a first-release requirement.

## 2. Architecture drivers

1. Prevent overlapping active bookings for the same provider/resource.
2. Make provider availability and customer booking understandable across timezones and daylight-saving transitions.
3. Support three roles: customer, service provider, platform administrator.
4. Enable iterative delivery with TDD and documented feature specifications.
5. Keep local development easy with SQLite while using PostgreSQL as the production source of truth.
6. Maintain clear seams for future payments, external calendars, messaging, and scaling.
7. Protect personal data and enforce server-side authorization.

## 3. Technology baseline

| Concern | Choice | Notes |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Vite | Composition API, Vue Router, Pinia where appropriate |
| Backend | FastAPI + Python | Versioned REST API |
| Validation | Pydantic | Request/response contracts |
| ORM | SQLAlchemy 2.x | Typed mappings and explicit transactions |
| Migrations | Alembic | All schema changes versioned |
| Local DB | SQLite | Development and fast tests only |
| Production DB | PostgreSQL | Authoritative transactional database |
| Backend tests | pytest | Unit, integration, contract, concurrency |
| Frontend tests | Vitest + Vue Test Utils | Component and composable tests |
| E2E | Playwright | Critical user journeys |
| API contract | OpenAPI | FastAPI-generated, reviewed |
| CI | Repository CI provider | Lint, type-check, tests, migration checks |
| Background work | Start with a database-backed/outbox worker or a small task worker | Select concrete technology in an ADR when required |
| Cache/broker | Not required initially | Add only for measured need |

Suggested frontend libraries (subject to ADR or dependency review): Vue Router, Pinia, a maintained form/validation library, and a maintained date/time library with IANA timezone support. Do not hand-roll timezone conversion.

## 4. Architectural style

### 4.1 Modular monolith

One backend application and one primary relational database, internally divided into domain modules. This provides straightforward transactions and deployment while preserving boundaries for future extraction.

### 4.2 Backend layers

- **API layer:** FastAPI routers, authentication dependencies, request parsing, response serialization.
- **Application layer:** use cases, orchestration, transaction boundaries, authorization checks.
- **Domain layer:** entities, value objects, policies, availability and booking invariants.
- **Infrastructure layer:** SQLAlchemy repositories, email/payment/calendar adapters, worker, external clients.

Domain modules should not import FastAPI or vendor-specific infrastructure. Infrastructure implements interfaces required by application/domain layers.

### 4.3 Suggested repository structure

```text
/
├── AGENTS.md
├── Task-List.md
├── README.md
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── router/
│   │   ├── modules/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── services/api/
│   │   └── stores/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── modules/
│   │   │   ├── identity/
│   │   │   ├── providers/
│   │   │   ├── services/
│   │   │   ├── availability/
│   │   │   ├── bookings/
│   │   │   ├── notifications/
│   │   │   ├── administration/
│   │   │   └── payments/       # introduced with payment phase
│   │   ├── infrastructure/
│   │   └── main.py
│   ├── migrations/
│   └── tests/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── SRS.md
│   ├── ROADMAP.md
│   ├── adr/
│   ├── features/
│   └── templates/
├── infra/
└── .github/workflows/
```

## 5. Context and main components

```text
Customer Browser       Provider Browser       Admin Browser
       |                      |                      |
       +----------------------+----------------------+
                              |
                        Vue 3 SPA
                              |
                       HTTPS / REST
                              |
                         FastAPI
                              |
       +----------------------+-----------------------+
       |                      |                       |
   Identity/RBAC          Scheduling              Administration
       |               +------+-------+                 |
       |               |              |                 |
   User/Profile      Services      Availability       Audit/Config
       |               |              |
       +---------------+--------------+
                              |
                       Booking Domain
                              |
                     SQLAlchemy / Unit of Work
                              |
                    PostgreSQL (production)
                    SQLite (local development)
                              |
                Outbox / Background Worker
                    |          |          |
                  Email    Calendar*   Payments*
```

`*` Optional later-phase integrations.

## 6. Domain model overview

Core entities and relationships (final schema is refined in feature specifications and ADRs):

- **User:** identity, email, password hash, status, locale, timezone, timestamps.
- **Role / Permission:** authorization capabilities. A user may hold more than one role where product policy allows.
- **ProviderProfile:** public profile, slug, biography, verification/approval state, default timezone.
- **Service:** provider-owned offering, title, description, duration, price, currency, buffers, active state, booking mode.
- **AvailabilityRule:** recurring weekly local-time window, timezone, effective dates.
- **AvailabilityException:** date-specific opening/closure or modified hours.
- **TimeOff:** provider absence interval.
- **Booking:** customer, provider, service snapshot, UTC start/end, status, price snapshot, policy snapshot, idempotency key.
- **BookingEvent:** append-only record of important state transitions.
- **Notification / OutboxMessage:** queued side effects and delivery state.
- **AuditLog:** actor, action, target, timestamp, request correlation, redacted metadata.
- **Payment:** optional later-phase payment intent/transaction/refund references; do not store raw card data.

Use explicit foreign keys, unique constraints, check constraints, indexes, and deletion policies. Prefer deactivation/soft deletion for records referenced by bookings.

## 7. Identity and authorization

Use role-based access control plus resource ownership checks.

- Customer: manage own profile and own bookings.
- Provider: manage only own provider profile, services, availability, and bookings assigned to them.
- Administrator: access platform administration according to explicit permission scopes.
- Public visitor: read only published provider profiles, active services, and public availability.

A role is not sufficient by itself. For example, provider endpoints must verify that the requested provider resource belongs to the authenticated provider. Administrative actions must be audited.

Authentication strategy (cookie session versus bearer/refresh token) must be selected in an ADR before implementation. For browser-first deployment, secure HttpOnly cookies are a strong default; include CSRF protection and SameSite policy. Never store long-lived credentials in localStorage.

## 8. Scheduling and availability design

### 8.1 Time model

- Persist actual appointment instants as UTC timestamps.
- Persist IANA timezone identifiers for providers and customers.
- Interpret recurring weekly availability in the provider's local timezone.
- Convert generated candidate intervals to UTC before comparison/persistence.
- Use a maintained timezone-aware library.
- Explicitly define behavior for nonexistent and ambiguous local times around daylight-saving transitions.
- API responses should include UTC instants and relevant timezone identifiers/local display data.

### 8.2 Availability calculation

A candidate slot is bookable only when all conditions hold:

1. It falls within an applicable provider availability rule.
2. It is not removed by a closure or time-off exception.
3. It satisfies service duration and pre/post buffers.
4. It satisfies minimum booking notice and maximum booking horizon.
5. It satisfies the provider's booking policy and any customer eligibility rules.
6. It does not overlap an active booking or a temporary hold.
7. It meets the slot increment/rounding policy.

The public availability endpoint is a read model. It cannot guarantee the slot remains free until the booking command commits.

## 9. Booking transaction and double-booking prevention

The booking use case must re-check all relevant conditions inside one database transaction. The final concurrency mechanism must be selected and recorded in an ADR before F-008 implementation.

Recommended PostgreSQL approach:

- Represent appointment occupancy using a half-open interval `[start_at, end_at)`.
- For single-capacity provider schedules, use a PostgreSQL exclusion constraint on provider/resource ID and a `tstzrange(start_at, end_at, '[)')` overlap operator, restricted to active states (for example pending hold and confirmed). `btree_gist` may be required.
- Alternatively, use a provider/resource row lock plus overlap query and transaction, but prove the invariant under concurrent requests. Do not use an application-only check.
- Ensure service buffers are included in the occupied interval or modeled in a way the constraint can enforce.
- Add an idempotency key unique per customer/request scope to make retries safe.
- Return a clear conflict response (HTTP 409) when a slot is no longer available.
- Commit booking and outbox notification records atomically.
- Dispatch email/calendar/payment work only after commit.

SQLite does not provide equivalent PostgreSQL exclusion/locking semantics. Keep fast tests on SQLite where portable, but run the concurrency suite against PostgreSQL in CI and before release.

## 10. Booking lifecycle

Initial suggested states:

- `PENDING_PROVIDER_CONFIRMATION` — provider must approve.
- `PENDING_PAYMENT` — optional payment phase only.
- `CONFIRMED` — accepted and reserved.
- `REJECTED`
- `CANCELLED_BY_CUSTOMER`
- `CANCELLED_BY_PROVIDER`
- `EXPIRED` — temporary hold expired.
- `COMPLETED`
- `NO_SHOW`

State transitions must be explicit and validated by a domain policy. Not every transition is legal. Store transition history in `BookingEvent`; do not silently overwrite important lifecycle events.

For instant-booking services, create a confirmed booking directly after all checks. For approval-based services, the pending state must still occupy the slot for a defined expiry window to avoid competing requests.

## 11. Database strategy

### 11.1 SQLite

- Default local development configuration.
- Useful for fast tests of portable business logic and basic persistence.
- Enable foreign-key enforcement for every connection.
- Use migrations in development just as in production.
- Do not rely on SQLite behavior for production concurrency, locking, JSON operators, or PostgreSQL-specific constraints.
- SQLite in-memory tests can behave differently depending on connection pooling; configure test engine/pool intentionally.

### 11.2 PostgreSQL

- Required for production.
- Required for authoritative booking concurrency tests.
- Required for migration validation and PostgreSQL-specific constraints.
- Use connection pooling appropriate to the deployment.
- Define backup, restore, retention, and upgrade procedures before production.

### 11.3 ORM and migrations

SQLAlchemy 2.x is the persistence abstraction. Alembic manages schema evolution. Keep domain logic independent of SQLAlchemy where practical. Never modify a released migration; add a new migration. Review generated migrations manually.

## 12. API design

- Base path: `/api/v1`.
- REST conventions and resource-oriented endpoints.
- OpenAPI is the API contract.
- Use Pydantic schemas for input/output.
- Standard error structure with stable machine-readable code, human-readable message, and optional field errors.
- Pagination for list endpoints.
- Use idempotency keys on booking creation and payment-related commands.
- Use ETags/version fields or explicit conflict handling for concurrent edits where needed.
- Use UTC ISO 8601 instants; include IANA timezone for local schedule operations.

Indicative endpoint groups:

- `/auth/*`, `/users/me`
- `/providers`, `/providers/me`, `/providers/{slug}`
- `/services`, `/providers/{provider_id}/services`
- `/providers/{provider_id}/availability`
- `/bookings`, `/bookings/{booking_id}`
- `/providers/me/bookings`
- `/admin/users`, `/admin/providers`, `/admin/settings`, `/admin/audit-logs`

Exact endpoint contracts belong in feature SPECs.

## 13. Frontend architecture

Vue 3 + TypeScript SPA. Organize by business module rather than only by technical file type. Use typed API clients. Keep server state distinct from ephemeral UI state. Use route guards for user experience but always enforce authorization on the backend.

Required UX states: loading, empty, validation error, server error, success, and retry. Accessibility target should be WCAG 2.2 AA as a product goal, validated progressively.

## 14. Notifications and background work

Start with email notifications for account verification, booking creation/confirmation/rejection/cancellation/rescheduling, and reminders. SMS/push are later options.

Use an outbox pattern when a committed booking must reliably trigger a notification. A worker claims pending outbox messages, sends through an adapter, and records attempts/results. Retries must be bounded and observable. Scheduled reminders need deduplication and timezone-safe scheduling.

## 15. Payments and external calendars

These are optional capabilities and should not block the first booking release unless business requirements demand them.

Payments:
- Use a payment provider adapter and hosted/tokenized payment UI.
- Never store card numbers or CVV.
- Treat signed webhooks as authoritative for asynchronous payment status.
- Make webhook processing idempotent.
- Define refund and cancellation policy before enabling payment.

Calendar integrations:
- Treat internal booking database as the source of truth.
- Use OAuth securely and least-privilege scopes.
- Track external event IDs and sync state.
- Handle retries, conflicts, token revocation, and provider-side edits explicitly.
- Do not let calendar sync silently create or confirm internal bookings.

## 16. Security, privacy, and compliance

Threat model at minimum: account takeover, privilege escalation, insecure direct object references, booking enumeration, brute force, CSRF/XSS, injection, webhook spoofing/replay, secret leakage, and personal-data overexposure.

Controls:
- Secure password hashing, email verification, password reset, rate limiting.
- Server-side RBAC and ownership checks.
- Secure cookies/CSRF controls or a documented token architecture.
- TLS in transit and encrypted backups/storage where available.
- Secrets management.
- Audit logs for privileged and sensitive operations.
- Data minimization, retention/deletion workflows, and export capability.
- Privacy notice and terms reviewed before launch.
- A formal legal review is required before making compliance claims.

## 17. Non-functional targets

Initial targets to validate and adjust with actual usage:

- Availability: design for 99.5% monthly service availability in the first production stage; raise only when justified.
- Performance: p95 API latency under 500 ms for ordinary read/write endpoints, excluding external integrations; public availability queries should be measured separately.
- Correctness: zero accepted overlapping active bookings for a single-capacity provider.
- Security: no known critical/high vulnerabilities at release.
- Recovery: define explicit RPO/RTO before production; initial proposal RPO ≤ 24 hours and RTO ≤ 8 hours, then tighten based on business need.
- Accessibility: target WCAG 2.2 AA.
- Maintainability: automated tests, migrations, linting, type checks, and documented operations.

These are proposed engineering targets, not measured guarantees.

## 18. Deployment view

Initial deployment may consist of:
- Static frontend hosting or a web server/CDN.
- FastAPI application behind a reverse proxy/load balancer.
- PostgreSQL.
- A background worker for outbox and reminders.
- SMTP/email provider.
- Centralized logs and basic metrics.
- Backup storage separate from the primary database.

Containerize services for repeatable development and deployment. Use environment-specific configuration and secrets. Do not commit production credentials. Build CI stages for lint/type-check/test/build/migration validation. Production deployment should use a reviewed migration-before/after strategy with rollback planning.

## 19. Architecture risks

| Risk | Impact | Mitigation |
|---|---|---|
| Double booking under concurrency | Critical | PostgreSQL constraint/locking, idempotency, concurrency tests |
| DST/timezone errors | High | IANA timezone model, explicit policy, boundary tests |
| SQLite/PostgreSQL behavior mismatch | High | PostgreSQL CI integration suite |
| Unauthorized access to another provider's data | Critical | Object-level authorization tests |
| Notification failure after booking | Medium | Transactional outbox, retry and monitoring |
| External calendar drift | Medium | Internal source of truth, sync state and reconciliation |
| Scope expansion | High | Feature intake gate, phased roadmap, non-goals |

## 20. ADR governance

Create one ADR for each material architecture decision. ADRs are immutable historical records: supersede rather than rewrite accepted decisions. At minimum, create ADRs for:
- Modular monolith and module boundaries.
- Authentication/session strategy.
- SQLite/PostgreSQL strategy.
- Booking overlap prevention and transaction model.
- Timezone and recurring schedule model.
- Outbox/background worker strategy.
- Payment and calendar integration choices when those phases begin.

## 21. Open decisions

The following product decisions must be resolved in relevant feature SPECs before implementation:
- Which provider categories and service types are supported?
- Is provider onboarding self-service, admin-approved, or both?
- Are bookings instant-confirmed, provider-approved, or configurable per service?
- Is payment required at booking, optional, or out of scope for the first release?
- Which currencies and locales are supported initially?
- Are group appointments/resources/capacity greater than one required?
- What are the cancellation, rescheduling, no-show, and refund policies?
- Are customer accounts mandatory, or can guest booking be supported?
- Which email/SMS and calendar providers are required?
