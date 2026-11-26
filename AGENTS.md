# AGENTS.md - Engineering Rules for AI Agents and Contributors

**Project:** BeautyBook - Online Salon Marketplace
**Status:** Initial engineering baseline (documentation phase)
**Last updated:** 2026-11-18

This file is mandatory reading before any change to the repository. It defines how work is
planned, specified, implemented, tested, reviewed, and documented. If an instruction in this
file conflicts with a direct instruction from the project owner for the current task, the
project owner wins. In every other case, this file and the approved feature documents win over
assumptions.

---

## 1. Product mission and context

BeautyBook is an online marketplace for beauty salons and hair salons. It has three primary
roles:

1. **Customer** - discovers salons, compares services and prices, views real availability, books
   appointments, and manages or cancels their own bookings.
2. **Salon Owner** - registers, creates and publishes a salon profile, manages services and
   prices, working hours, unavailable periods, photos and portfolio images, and the salon's
   appointments.
3. **Administrator** - manages users, salons, platform settings, moderation, support actions, and
   audit records.

A public visitor (not signed in) can browse published salon profiles, services, prices, and
advertised availability. Whether a visitor may book without an account is an open product
decision (see `docs/SRS.md`, Section 13).

The product is not "just a calendar UI". The following are correctness-critical:

- Two customers must never end up with overlapping active appointments at the same salon.
- A salon owner must never read or modify another owner's data.
- A customer must never read or modify another customer's bookings.
- Times must remain correct across timezones and daylight-saving changes.
- Money must never be stored or calculated with binary floating point.
- Uploaded images must be validated and served safely.
- Privileged actions must be auditable.

Your job is to make the smallest correct, secure, maintainable change that satisfies an approved
specification. Do not silently expand scope.

---

## 2. Source-of-truth hierarchy

When documents or instructions conflict, use this order:

1. Explicit instruction from the project owner for the current task.
2. Approved feature `SPEC.md`.
3. Approved feature `PLAN.md`.
4. Accepted ADRs in `docs/adr/`.
5. `docs/SRS.md` and `docs/ARCHITECTURE.md`.
6. `docs/ROADMAP.md`, `Task-List.md`, and existing tests.
7. Existing implementation.
8. Your own assumptions.

Never treat an assumption as an approved requirement. Record unresolved questions in the feature
specification and ask the project owner when the answer affects data integrity, security,
user-visible behavior, cost, or scope.

---

## 3. Non-negotiable project rules

These rules apply to every task, including "small" changes:

1. **No unregistered feature work.** Every feature must be registered in `Task-List.md` before
   implementation starts.
2. **Every feature has a SPEC and a PLAN.** Create `docs/features/<TASK-ID>-<short-name>/SPEC.md`
   and `PLAN.md`. Do not create empty placeholder documents to bypass the gate.
3. **Every material architectural decision has an ADR.** Record it in `docs/adr/`. If no ADR is
   needed, state why in the feature `PLAN.md`.
4. **Practice TDD.** Write a failing test first (Red), implement the minimum code to pass
   (Green), then refactor (Refactor).
5. **Tests come before feature logic.** Do not implement first and bolt on superficial tests
   afterwards.
6. **Never claim a test passed unless you actually ran it and saw it pass.** Report the exact
   command and result. Never fabricate output.
7. **Keep frontend and backend responsibilities separate.** The frontend renders and validates
   for usability; the backend is authoritative for authorization, pricing, availability, and
   state changes.
8. **Never hardcode passwords, API keys, tokens, or other secrets.** Use environment variables
   and documented configuration. `.env` files must never be committed.
9. **Use environment variables for sensitive or environment-specific configuration.**
10. **Update documentation when implementation changes the agreed design.** A change that makes
    documentation wrong is incomplete until the documentation is fixed.
11. **Do not implement multiple unrelated features in one task.** One task, one coherent change.
12. **Ask for clarification when an important requirement is ambiguous.** Stop rather than guess
    when the guess could hurt data integrity or users.
13. **Do not silently change the agreed technology stack.** A material addition or replacement
    needs an ADR, a stated reason, and explicit approval.
14. **Preserve existing user work.** Inspect before deleting or overwriting. Never remove files
    merely to make the repository look cleaner.
15. **Do not add dependencies casually.** Explain why, check maintenance and security, and update
    the ADR when the dependency is material.
16. **Do not leave dead code, unused dependencies, or TODO comments as a substitute for work.**
    Deferred work must be a tracked task.
17. **Do not weaken or skip a failing test to get a green build.**
18. **Do not expose secrets, personal data, or internal errors in logs or API responses.**

---

## 4. Mandatory feature intake gate

Before writing feature code:

1. Read this file, `docs/SRS.md`, `docs/ARCHITECTURE.md`, relevant ADRs, the existing code, and
   the existing tests.
2. Add the feature to `Task-List.md` with:
   - unique task ID (`F-###`),
   - clear title and owning module,
   - priority (`P0`-`P3`),
   - status,
   - dependencies,
   - links to the future `SPEC.md` and `PLAN.md`.
3. Create the feature folder: `docs/features/<TASK-ID>-<short-name>/`.
4. Write `SPEC.md` using `docs/templates/SPEC-TEMPLATE.md`. Include:
   - problem and objective,
   - actors and permissions,
   - user journeys and failure paths,
   - in-scope and out-of-scope items,
   - testable functional requirements,
   - business rules and invariants,
   - API and UI behavior,
   - data impact,
   - security and privacy impact,
   - edge cases,
   - measurable acceptance criteria,
   - test strategy,
   - open questions.
5. Write `PLAN.md` using `docs/templates/PLAN-TEMPLATE.md`. Include:
   - ordered implementation steps,
   - the tests to write first,
   - file/module changes,
   - migration and rollback plan,
   - documentation changes,
   - risks and mitigations,
   - completion checklist.
6. Decide whether an ADR is required. Create it before implementation when the decision changes
   system boundaries, persistence, consistency, security, deployment, an external integration, or
   a long-lived dependency.
7. Request approval when the work changes product behavior, data contracts, security, or
   architecture.
8. Only then start TDD implementation.

A bug fix may use a lighter-weight entry, but it still needs a reproducible failing test and a
documented expected behavior. Any behavior change is a feature for the purposes of this gate.

---

## 5. Required development method: TDD

Use Red -> Green -> Refactor for every behavior change:

1. **Red:** Write a focused test that expresses the required behavior. Run it. Confirm it fails
   for the expected reason, not because of a typo or missing import.
2. **Green:** Write the minimum code that makes the test pass. Do not add speculative features.
3. **Refactor:** Improve names, structure, and duplication while keeping all tests green.
4. **Regression:** Add a test for every defect you fix.
5. **Verify:** Run the focused tests, then the relevant broader suite.

### Test layers

- **Unit tests:** pure business rules, validation, price calculations, availability arithmetic,
  state transitions, permission policies.
- **Integration tests:** repositories, transactions, API endpoints, migrations, image storage
  adapters, email adapters.
- **Contract tests:** request/response schemas and OpenAPI compatibility.
- **End-to-end tests:** critical customer, owner, and admin journeys in a browser.
- **Security tests:** authentication boundaries, object-level authorization (IDOR), input
  validation, rate limits, upload validation, CSRF.
- **Concurrency tests:** simultaneous booking attempts for the same salon interval. These must
  run against PostgreSQL.

### Honesty about test environments

SQLite is acceptable for fast, portable tests. It is **not** proof of production booking
concurrency. If PostgreSQL is unavailable in the current environment, say so explicitly and mark
the concurrency verification as not run. Do not substitute an SQLite result and call it
production-grade evidence.

---

## 6. Architecture principles

### 6.1 Modular monolith

Build one FastAPI backend with explicit domain modules and one primary PostgreSQL database. Do not
introduce microservices, event sourcing, CQRS, a message broker, or distributed locking without a
measured need and an approved ADR.

Modules:

- `identity` - registration, login, sessions, email verification, password reset.
- `users` - user profiles, roles, account status, preferences.
- `salons` - salon profile, address, contact details, publishing state, public profile.
- `services` - salon services, duration, price, currency, buffers.
- `portfolio` - salon photos and portfolio image metadata and storage.
- `availability` - weekly working hours, time off, availability calculation.
- `bookings` - booking lifecycle, conflict prevention, idempotency, history.
- `notifications` - outbox, email delivery, reminders.
- `administration` - admin users, salon moderation, platform settings, audit log.

`identity` and `users` may be combined in F-001 if the team documents the decision.
Do not create modules that have no concrete responsibility.

### 6.2 Backend layers inside each module

Use a consistent, simple internal layout:

```text
backend/app/modules/<module>/
  domain.py       # framework-free rules, value objects, policies
  models.py       # SQLAlchemy 2.x mappings
  schemas.py      # Pydantic request/response schemas
  repository.py   # persistence queries
  service.py      # use cases and transaction boundaries
  router.py       # HTTP endpoints only
```

Dependency direction:

```text
router -> service -> repository / domain
                   -> other module's public service (when necessary)
```

Rules:

- `domain.py` must not import FastAPI, SQLAlchemy, or HTTP concerns.
- Routers parse HTTP, resolve the authenticated user, call one use case, and map the result.
- Services own transaction boundaries and authorization checks.
- Repositories contain queries, not business decisions.
- Do not import another module's ORM models. Reference other entities by ID and call the owning
  module's public service/query function.
- Do not create cyclic module dependencies. If two modules need each other, introduce a small
  shared interface or move the shared rule to the correct owner.
- Cross-module reporting/read queries may live in a dedicated read module only when documented in
  the feature spec.

### 6.3 Frontend structure

Organize by business module, not only by file type:

```text
frontend/src/
  app/            # bootstrap, layouts, global providers
  router/         # routes and guards
  modules/        # auth, salons, services, booking, dashboards, admin
  components/     # genuinely shared presentational components
  composables/    # shared reusable composition functions
  services/api/   # typed HTTP client and endpoint wrappers
  stores/         # Pinia stores for shared client state only
  assets/styles/  # design tokens and global styles
```

- Keep page components thin. Put data loading in composables/API wrappers and shared state in
  Pinia only when multiple screens need it.
- Do not mirror all server data into global stores.
- Do not put authorization decisions only in the UI.
- Do not duplicate backend business rules in the frontend.

---

## 7. Backend rules

- Use Python type hints throughout production code.
- Use FastAPI routers only for HTTP concerns: parsing, auth context, response mapping, status
  codes.
- Use Pydantic schemas for all request and response bodies. Never return ORM objects directly.
- Use SQLAlchemy 2.x typed mappings and explicit session/transaction handling.
- Keep database sessions request-scoped and close them reliably.
- Use Alembic for every schema change. Never use `create_all()` as the production migration
  strategy.
- Enforce referential integrity, unique constraints, check constraints, and foreign keys in the
  database, not only in Python.
- Use UTC-aware datetimes. Never store naive timestamps for appointment instants.
- Use `zoneinfo` (or an equivalent maintained timezone library) for IANA timezone handling. Do not
  hand-roll timezone conversion.
- Represent money as integer minor units plus an ISO 4217 currency code. Never use `float` for
  money.
- Use stable, machine-readable error codes and one consistent error envelope.
- Validate ownership and role permissions server-side on every protected operation.
- Use pagination for potentially unbounded lists.
- Use idempotency keys for booking creation and other retry-sensitive commands.
- Do not perform network calls (email, storage, payments) while holding a database transaction or
  row lock.
- Avoid N+1 queries; eager-load or batch where the read path needs it.
- Do not log passwords, session tokens, reset tokens, full personal data, or image contents.

---

## 8. Frontend rules

- Use Vue 3 Composition API, TypeScript, and `<script setup>`.
- Use Vue Router for navigation and Pinia for shared client state.
- Use a typed API client. Do not scatter raw `fetch` calls across components.
- Centralize authentication handling, error mapping, and request correlation.
- Validate forms for usability, but treat backend validation as authoritative.
- Provide loading, empty, success, error, and retry states for every data-driven screen.
- Make the UI responsive and mobile-first.
- Meet accessibility basics: semantic HTML, labels, keyboard navigation, visible focus, sufficient
  contrast, and accessible error messages. Target WCAG 2.2 AA.
- Do not store long-lived credentials in `localStorage` or `sessionStorage`.
- Do not commit secrets or environment-specific URLs to the frontend bundle.
- Avoid `any` unless there is a documented reason.
- Keep components small and focused; extract repeated UI into shared components.

---

## 9. Domain rules

### 9.1 Users and roles

- Every account has a unique, normalized email address.
- Email ownership must be verified before sensitive account actions.
- A user may hold more than one role in the data model, but the MVP UI may expose one primary
  role. Do not assume a single-role schema unless the ADR/spec says so.
- An administrator role does not automatically make every action acceptable: privileged actions
  still require explicit permission checks and audit records.

### 9.2 Salons

- A salon belongs to exactly one owner in the MVP. Ownership transfer is an administrator-only,
  audited action.
- One owner may have one salon in the MVP unless the product decision changes. Enforce this with a
  database constraint while it is true.
- A salon has a unique public slug, a name, a description, an address, contact details, an IANA
  timezone, and a publishing status.
- Only published, non-suspended salons and their active services are publicly visible.
- Salon edits must never silently change historical booking snapshots.
- Ownership and role checks are mandatory for every owner endpoint.

### 9.3 Services and pricing

- A service belongs to exactly one salon.
- A service has a name, duration in minutes, price in integer minor units, an ISO 4217 currency,
  optional description, optional buffers, and an active flag.
- Duration must be positive. Price must be zero or positive.
- Deactivating or archiving a service must not delete historical bookings.
- Changing a service price or duration must not rewrite existing bookings.

### 9.4 Portfolio images

- Validate file content (magic bytes), not only the filename extension.
- Allow only explicitly permitted image types (initially JPEG, PNG, WebP).
- Enforce a maximum file size.
- Store files outside the web root with random, non-guessable keys.
- Never trust a client-supplied storage path.
- Strip unnecessary metadata (including location EXIF) before public serving where practical.
- Only the owning salon can add, reorder, replace, or delete its images.
- Deleting an image must not break a historical record that references it; use soft deletion or a
  documented replacement policy.

### 9.5 Reviews

Customer reviews are **planned for a future phase**. Do not implement reviews, ratings, or
moderation before the review task is Ready. When implemented, only a customer with a completed
booking may review that salon, and moderation rules must be specified.

---

## 10. Booking and time correctness rules

These are the most important rules in the project:

- A salon must never have two active bookings whose occupied intervals overlap, unless a future
  approved feature explicitly adds capacity greater than one (for example, multiple staff or
  rooms).
- Availability shown to a customer is **advisory**. The booking command must revalidate
  availability inside the authoritative database transaction.
- Use half-open intervals `[start, end)`. A booking ending at 10:30 does not conflict with one
  starting at 10:30.
- Persist appointment instants in UTC. Persist the salon's IANA timezone for interpreting working
  hours and displaying local time.
- Working hours are recurring local-time rules in the salon's timezone. Convert candidate slots to
  UTC before comparison and persistence.
- Include service duration, pre/post buffers, time off, minimum notice, booking horizon, and
  cancellation cutoffs in availability and booking checks.
- Model the **occupied interval** explicitly. If a service has buffers, the blocked interval is
  larger than the service interval. The overlap constraint must use the blocked interval.
- Use a PostgreSQL exclusion constraint (or an equivalent proven row-lock design) as the final
  protection against double booking. An application-only "check then insert" is not sufficient.
- Use an idempotency key so a client retry returns the original booking instead of creating a
  second one.
- A booking must preserve a snapshot of material terms at creation: service name, duration,
  price, currency, salon timezone, and the applicable cancellation policy.
- Define and validate the booking state machine. Not every transition is legal.
- Record important booking transitions in an append-only `booking_events` table.
- Define DST behavior: nonexistent local times are skipped; ambiguous local times use an explicit
  documented convention (initially the first occurrence, `fold=0`). Test both.
- Never rely on frontend checks to prevent double booking.

The final concurrency design must be recorded in `docs/adr/0003-booking-concurrency.md` and
verified with concurrent PostgreSQL integration tests before F-009 is marked Done.

---

## 11. Security and privacy baseline

- Deny by default. Apply least privilege.
- Enforce role permissions and resource ownership in backend use cases, not only in routes or the
  UI.
- Hash passwords with Argon2id via a maintained library. Never write custom cryptography.
- Browser sessions should use secure, `HttpOnly`, `SameSite` cookies where feasible. If bearer
  tokens are used, document refresh, revocation, storage, and CSRF/XSS mitigations in an ADR.
- Protect state-changing cookie-authenticated requests against CSRF.
- Rate-limit login, registration, password reset, public availability, and booking endpoints.
- Use short-lived, single-use password-reset and email-verification tokens. Store only token
  hashes where possible.
- Verify email ownership before enabling sensitive account actions.
- Validate uploads by content type, size, and actual bytes. Serve them from a controlled origin or
  endpoint.
- Keep secrets out of source control and out of frontend bundles.
- Audit privileged actions and important booking state transitions.
- Define retention, export, and deletion behavior for personal data before production.
- Do not claim legal compliance (GDPR or otherwise) without a documented legal and operational
  review.

---

## 12. Database and migrations

- PostgreSQL is the default application database for development, integration tests,
  concurrency tests, and production.
- SQLite is also accepted for a local, single-operator setup (ADR-0011). The engine enables
  foreign keys and reads timestamps back as UTC, but SQLite cannot provide the booking exclusion
  constraint or multi-writer concurrency; those tests still run on PostgreSQL.
- SQLite must not be presented as production-equivalent for booking correctness.
- Use SQLAlchemy 2.x and Alembic.
- Every schema change needs a migration. Do not modify a released migration; add a new one.
- Keep migrations deterministic and review generated SQL manually.
- Test migrations from the previous released schema against PostgreSQL.
- Prefer portable SQL where practical. Isolate PostgreSQL-specific features (exclusion
  constraints, `btree_gist`, JSONB operators) behind migrations/repositories and document them.
- Use soft deletion/deactivation for entities referenced by bookings or audit records.
- Add indexes for common lookups: salon + time range, customer + time range, salon + status,
  service + active state, unique email, unique salon slug.

---

## 13. API conventions

- Base path: `/api/v1`.
- Use resource-oriented REST endpoints and explicit request/response schemas.
- Use ISO 8601 UTC instants (`...Z` or explicit offset) for appointment times.
- Return IANA timezone identifiers separately where local schedule semantics matter.
- Use consistent pagination and filtering.
- Use a consistent error envelope:

```json
{
  "error": {
    "code": "SLOT_UNAVAILABLE",
    "message": "The selected time is no longer available.",
    "fields": {},
    "request_id": "..."
  }
}
```

- Return `409 Conflict` for booking conflicts, `422` for validation errors, `401` for missing or
  invalid authentication, and `403` for authenticated but unauthorized requests.
- Keep OpenAPI accurate. Review schema changes as part of the feature.
- Do not make breaking API changes without a documented migration/deprecation plan.

Indicative endpoint groups (exact contracts belong in feature specs):

- `/auth/*`, `/users/me`
- `/salons`, `/salons/{slug}`, `/salons/{slug}/services`, `/salons/{slug}/availability`
- `/owner/salon`, `/owner/salon/services`, `/owner/salon/working-hours`,
  `/owner/salon/time-off`, `/owner/salon/photos`, `/owner/bookings`
- `/bookings`, `/bookings/{id}`, `/bookings/{id}/cancel`
- `/admin/users`, `/admin/salons`, `/admin/settings`, `/admin/audit-logs`

---

## 14. Documentation duties

- `Task-List.md` is the single delivery queue. Update it when a task starts, becomes blocked, or
  is completed.
- Each feature has a `SPEC.md` and `PLAN.md` under `docs/features/`.
- Each material decision has an ADR under `docs/adr/`. ADRs are historical records: supersede
  them rather than rewriting accepted decisions.
- If implementation changes the architecture, data model, API, security posture, or user-visible
  behavior, update the relevant documentation in the same task.
- Keep the README honest about what exists and what does not.

---

## 15. Verification and honesty

Before claiming completion:

- Run the formatter and linter.
- Run type checks.
- Run focused tests, then the relevant full suite.
- Run PostgreSQL integration/concurrency tests when the change touches persistence or booking
  correctness.
- Review migration upgrade and rollback behavior.
- Check authorization, validation, privacy, and error paths.
- Update `Task-List.md`, the feature `PLAN.md`, and affected documentation.

In the completion report, state:

- what changed,
- which commands were actually executed,
- the exact results,
- what was **not** run and why,
- known limitations,
- follow-up tasks.

"It should work" is not verification. "I did not run this because PostgreSQL is not installed in
this environment" is acceptable honesty.

---

## 16. Definition of Ready (DoR)

A feature is Ready only when:

- It has a unique entry in `Task-List.md`.
- Its `SPEC.md` and `PLAN.md` exist and are reviewed.
- The user journey and acceptance criteria are objectively testable.
- Dependencies, non-goals, and open questions are explicit.
- Data, API, authorization, privacy, and operational impacts are identified.
- Required ADRs exist, or the plan explains why none is needed.
- The test strategy is defined, including PostgreSQL/concurrency tests where relevant.

Do not start implementation while the task is `Proposed`, `Specifying`, or `Review`.

---

## 17. Definition of Done (DoD)

A feature is Done only when:

- All acceptance criteria pass.
- TDD evidence exists in the test suite.
- Unit, integration, and relevant end-to-end tests pass.
- PostgreSQL-specific and concurrency tests pass where applicable.
- Authorization, validation, error, and edge cases are covered.
- Migrations and rollback notes are complete.
- API documentation and user-facing behavior are updated.
- Logs/metrics are adequate for operations.
- No known critical security or data-integrity defect remains.
- `Task-List.md` and the feature `PLAN.md` are updated.
- The completion report is honest and complete.

---

## 18. Required workflow for every task

### Before editing

- Inspect the repository structure, relevant modules, tests, and documentation.
- Read the linked SPEC, PLAN, and ADRs.
- Confirm the task is approved and not blocked.
- State assumptions and the files you expect to change.

### During work

- Follow Red -> Green -> Refactor.
- Keep changes scoped to the task.
- Update tests, API schemas, migrations, and documentation together.
- Never fabricate command output or claim tests ran if they did not.

### Before completion

- Run the verification steps in Section 15.
- Review the diff for accidental scope creep.
- Report exactly what changed and what remains.

---

## 19. Agent communication protocol

For each task, report:

1. Task ID and linked specification.
2. Your understanding of the expected behavior.
3. Assumptions and unresolved questions.
4. Planned files/modules and tests.
5. Implementation summary.
6. Tests and commands actually executed, with results.
7. Migration/operational impact.
8. Remaining risks or follow-up tasks.

If asked to implement a feature without a SPEC/PLAN, stop at the intake gate and create or request
approval for those documents. Do not bypass the gate because the change "looks small".

---

## 20. Forbidden shortcuts

Do not:

- implement booking logic only in the frontend,
- rely on a "SELECT then INSERT" check as the only double-booking protection,
- use `float` for money,
- store naive datetimes for appointments,
- trust a filename extension as proof of image type,
- return raw ORM objects from API endpoints,
- put business rules in Vue components or FastAPI route handlers,
- create a shared "utils" dumping ground for unrelated logic,
- disable a test to make CI pass,
- commit `.env` files or real credentials,
- add a new framework, state library, UI kit, queue, or cloud service without an ADR and approval,
- delete existing user content to simplify your own work,
- mark a task Done without running the relevant verification.

---

## 21. Beginner-friendly communication

The project owner is learning. When you make a non-obvious decision, explain it briefly in plain
language:

- what problem it solves,
- why this option was chosen,
- what the trade-off is.

Keep explanations short and concrete. Prefer a small example over abstract theory. Do not hide
uncertainty; say what is known, what is assumed, and what must be tested.
