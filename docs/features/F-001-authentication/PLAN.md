# Implementation Plan - F-001 Authentication and Registration Gate

- **Status:** Ready - approved 2026-11-18; implementation in progress
- **Related SPEC:** [`SPEC.md`](./SPEC.md)
- **Related ADRs:** ADR-0010 (registration flows and role assignment, accepted), ADR-0005 (session
  strategy, accepted), ADR-0009 (authorization model), ADR-0002 (PostgreSQL), ADR-0001 (modular
  monolith)
- **Owner:** BeautyBook project owner and engineering agent
- **Last updated:** 2026-11-19

---

## 1. Implementation approach

Build the first **vertical slice** of BeautyBook: a minimal runnable application plus the
registration gate - customer signup, salon-owner application, administrator approval, login,
logout, sessions, role checks, protected routes, and the matching frontend pages.

### Backend boundaries

- Identity, roles, sessions, and owner applications live in the `identity` module for now.
  `users` is not split into its own module; the architecture explicitly allows merging them if
  documented.
- `identity` owns `users`, `user_roles`, `sessions`, and `owner_applications`.
- The HTTP layer stays thin: parse, resolve the session, call one use case, map the response.
- Transaction boundaries live in `identity/service.py`.
- Password hashing, token generation, and CSRF primitives live in `core/security.py` and are
  injected where practical so tests can control cost.
- Database access lives in `identity/repository.py`.
- The administrator bootstrap CLI lives in `app/cli.py`, is registered only as a module entry
  point, and is never mounted on the HTTP app.

### Registration gate mechanism

- Two explicit endpoints, one per trust path. No role field exists in either schema.
- Customer flow: `active` user + `customer` role + session, in one transaction.
- Owner flow: `pending_approval` user + `customer` base role + `pending` application, in one
  transaction. No session and no `salon_owner` role.
- Approval: row-locked application + conditional update + user activation + `salon_owner`
  insertion, in one transaction.
- Rejection: row-locked application + conditional update + user rejection, in one transaction.

### Authentication mechanism

- Database-backed sessions (ADR-0005).
- Opaque random session token in an `HttpOnly` cookie.
- SHA-256 hash of the token stored in `sessions.token_hash`.
- Argon2id password hashing.
- Double-submit CSRF token for all state-changing requests.
- Generic login errors; status codes revealed only after password verification.

### Frontend boundaries

- `modules/auth` contains registration, login, account, and pending pages.
- `modules/admin` contains the minimal owner-application review page. It is deliberately small and
  will be replaced by F-014.
- `modules/owner` contains the `/owner` placeholder.
- `stores/auth.ts` holds the current user and auth actions.
- `services/api` owns the typed HTTP client, CSRF header handling, and error mapping.
- `router` owns public/protected/role route metadata and guards.
- No session token is stored in JavaScript-accessible storage.

### What is deliberately not built

- No full salon profile, services, prices, portfolio, working hours, booking, owner appointment
  dashboard, email verification, password reset, rate limiting, role revocation, persistent audit
  table, or full administration. These belong to F-002 through F-018.

### Foundation scope control

F-001 must create enough infrastructure to run and test the feature, but not a full production
platform. The foundation is limited to:

- dependency and project configuration,
- configuration loading and validation,
- PostgreSQL connection and session management,
- one initial Alembic migration,
- `/health` and `/ready`,
- request-id logging,
- pytest and Vitest harnesses,
- a minimal CI workflow,
- a documented local run path.

Anything beyond that is F-018.

---

## 2. Preconditions

- [x] F-000 documentation baseline is complete.
- [x] F-001 SPEC is approved by the project owner, including the two-flow registration decision.
- [x] This PLAN is approved by the project owner.
- [x] ADR-0010 (registration flows and role assignment) is accepted.
- [x] ADR-0005 (session strategy) is accepted.
- [x] PostgreSQL is available locally (native PostgreSQL 16.16 verified).
- [x] Python 3.12+ and Node.js 20+ are installed (Python 3.14.4, Node.js 26.13.1).
- [x] The task is moved to `Ready` in `Task-List.md`.

The documentation preconditions are met (2026-11-18). Implementation may begin once the local
toolchain and PostgreSQL are verified. Environment checks are performed, not assumed.

---

## 3. Ordered TDD tasks

Each step is a Red -> Green -> Refactor increment. Write the listed test first, run it, confirm it
fails for the expected reason, then implement the minimum.

### Step 0 - Minimal application foundation

| Item | Detail |
|---|---|
| Tests first | `tests/unit/test_config.py` (missing/invalid settings fail clearly; safe defaults), `tests/integration/test_health.py` (`/health` returns 200, `/ready` checks DB), `tests/unit/test_app_import.py` (app factory imports without side effects), `tests/unit/test_cli_boundary.py` (CLI module is not mounted as a route). Frontend: `tests/unit/app.spec.ts` (app mounts, router renders login). |
| Backend files | `pyproject.toml`, `app/main.py`, `app/cli.py`, `app/core/config.py`, `app/core/errors.py`, `app/core/logging.py`, `app/infrastructure/database.py`, `app/api/v1/router.py`, `app/api/v1/health.py` |
| Frontend files | `package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`, `src/main.ts`, `src/app/App.vue`, `src/router/index.ts`, `src/assets/styles/tokens.css`, `src/assets/styles/global.css`, `vitest.config.ts` |
| Infra files | `compose.yaml` or `infra/docker-compose.yml` for PostgreSQL, `.env.example`, `.github/workflows/ci.yml` |
| Refactor | Keep bootstrap small; no speculative abstractions. |

**Acceptance for this step:** backend starts, `/health` and `/ready` work, PostgreSQL connection is
verified, frontend builds and mounts, the test commands run, and `python -m app.cli --help` works.

### Step 1 - Domain rules

| Item | Detail |
|---|---|
| Tests first | `tests/unit/test_email_normalization.py` (trim, lowercase, valid/invalid, max length), `tests/unit/test_password_policy.py` (11/12/128/129 chars, whitespace-only, Unicode, no composition rules), `tests/unit/test_roles.py` (valid roles, customer base role, no admin from registration), `tests/unit/test_user_status.py` (allowed statuses and transitions), `tests/unit/test_owner_application_policy.py` (pending -> approved/rejected only; rejection requires a reason), `tests/unit/test_locale_values.py` (IANA timezone and ISO 4217 currency validation), `tests/unit/test_safe_redirect.py`. |
| Files | `app/modules/identity/domain.py` |
| Green | Pure functions/value objects: normalize email, validate password, role constants, status enums and transitions, application state machine, timezone/currency checks, safe redirect helper. |
| Refactor | No FastAPI or SQLAlchemy imports in `domain.py`. |

### Step 2 - Models and initial migration

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_auth_models.py`: unique email (case-normalized), status check constraint, role check constraint, unique session token hash, unique application per user, application status/review constraints, cascade behavior for roles/sessions/applications, UUID primary keys. |
| Files | `app/modules/identity/models.py`, `migrations/versions/0001_authentication.py`, `migrations/env.py`, `alembic.ini` |
| Green | `users`, `user_roles`, `sessions`, and `owner_applications` with constraints and indexes. |
| Refactor | Generate UUIDs in Python to avoid a PostgreSQL extension dependency. |

**Migration verification:** run `alembic upgrade head`, `alembic downgrade base`,
`alembic upgrade head` on a disposable PostgreSQL database before proceeding.

### Step 3 - CSRF primitives and dependency

| Item | Detail |
|---|---|
| Tests first | `tests/unit/test_csrf.py` (random token length, constant-time compare), `tests/integration/test_auth_csrf.py` (token endpoint sets cookie; missing/mismatch header -> 403; valid header passes a test-only route; rejection happens before any write). |
| Files | `app/core/security.py`, `app/modules/identity/dependencies.py`, `app/modules/identity/router.py` (`GET /auth/csrf`) |
| Green | Issue token, set cookie, compare cookie/header, raise `CSRF_INVALID`. |
| Refactor | Extract cookie names and flags into config. |

### Step 4 - Session service

| Item | Detail |
|---|---|
| Tests first | `tests/unit/test_session_policy.py` (expiry boundary, revoked, non-active user), `tests/integration/test_session_repository.py` (raw token not stored, hash lookup, revoke current only, multiple sessions). |
| Files | `app/modules/identity/service.py`, `app/modules/identity/repository.py` |
| Green | Create session, validate session, revoke session, hash token with SHA-256. |
| Refactor | Inject clock/hasher for deterministic tests. Sessions are created only for `active` users. |

### Step 5 - Customer registration

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_register_customer.py`: 201 + cookies, `customer` role, `status=active`, email normalized, duplicate 409, validation 422, unknown `role`/`status` field 422, no password hash in response, no plaintext in DB, and `tests/concurrency/test_registration_race.py` for two simultaneous registrations. |
| Files | `app/modules/identity/schemas.py`, `service.py`, `repository.py`, `router.py` |
| Green | Validate, hash, insert user + customer role + session atomically, set cookies, return safe user. |
| Refactor | Keep transaction ownership in the service; map unique violation to `409`. |

### Step 6 - Salon-owner application

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_register_owner.py`: 202 and **no** session cookie, `status=pending_approval`, pending application row, **no** `salon_owner` role, salon basics persisted, invalid timezone/currency 422, duplicate email against both customer and owner flows 409, unknown privileged fields 422, no public exposure of application data. Concurrency: two simultaneous owner applications for one email -> one 202, one 409. |
| Files | `schemas.py`, `service.py`, `repository.py`, `router.py` |
| Green | Validate, hash, insert pending user + base customer role + pending application atomically, return 202 without cookies. |
| Refactor | Reuse the shared validation and hashing path with customer registration; keep the transaction in the service. |

### Step 7 - Login and account status

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_auth_login.py`: active 200, wrong password 401, unknown email 401 (same body), pending 403 `ACCOUNT_PENDING_APPROVAL`, rejected 403 `ACCOUNT_REJECTED`, suspended 403 `ACCOUNT_SUSPENDED`, status codes only after a correct password, case-insensitive email, session rotation, Argon2id verification, optional rehash path. |
| Files | `schemas.py`, `service.py`, `router.py` |
| Green | Verify credentials, dummy hash for unknown email, reject non-active status, create session only for active users. |
| Refactor | Share cookie-setting logic with customer registration; keep the error mapping in one place. |

### Step 8 - Current user and role dependency

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_auth_me.py`: 200 with valid cookie, 401 missing/malformed/expired/revoked, 401 for a user who became non-active, response contains roles and status and no secrets, roles are read from the database. `tests/integration/test_authorization.py`: `require_roles` returns 403 for a missing role and allows a present role. |
| Files | `dependencies.py`, `router.py` |
| Green | Resolve session from cookie, load user, expose `CurrentUser`; implement `require_roles(*roles)`. |
| Refactor | One dependency for session resolution; avoid duplicate queries; no role caching in the session. |

### Step 9 - Logout

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_auth_logout.py`: 204, session revoked, cookie cleared, CSRF required, second logout 401, other sessions remain valid. |
| Files | `service.py`, `router.py` |
| Green | Revoke current session, clear cookies. |
| Refactor | Keep logout idempotent from the UI's perspective while the API remains strict. |

### Step 10 - Administrator bootstrap CLI

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_cli_create_admin.py`: creates an active admin with `admin` + `customer` roles, refuses a duplicate email without changing data, rejects a weak password, reads the password from stdin, and does not accept a password argument. `tests/unit/test_cli_boundary.py` asserts the command is absent from the HTTP route table. |
| Files | `app/cli.py`, `app/modules/identity/service.py`, `app/modules/identity/repository.py` |
| Green | `create-admin` command; interactive/stdin password; Argon2id hashing; atomic user + roles insert. |
| Refactor | Reuse the same user-creation service path as registration; keep the CLI thin. |

### Step 11 - Administrator role grant

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_admin_role_grant.py`: admin grants `admin` and `salon_owner`; non-admin 403; unauthenticated 401; CSRF required; non-active target 409; duplicate grant idempotent; `customer` and unknown role 422; no self-grant through a public route. |
| Files | `schemas.py`, `service.py`, `router.py` (`POST /admin/users/{user_id}/roles`) |
| Green | Validate role, load target, require active, insert idempotently, emit audit event, return updated user. |
| Refactor | Keep the grantable-role allowlist in `domain.py`; do not add revocation yet. |

### Step 12 - Administrator application review

| Item | Detail |
|---|---|
| Tests first | `tests/integration/test_admin_owner_applications.py`: list pending with pagination and order; approve activates user + adds role + records reviewer; reject stores reason + rejects user + adds no role; reject without reason 422; review of a reviewed application 409; non-admin 403; CSRF required; audit event emitted without personal data. `tests/concurrency/test_approval_race.py`: two simultaneous approvals -> one success, one 409, one role row. |
| Files | `schemas.py`, `service.py`, `repository.py`, `router.py` (`/admin/owner-applications`) |
| Green | List with filters; approve and reject with `SELECT ... FOR UPDATE` plus conditional status update; atomic writes; audit logging. |
| Refactor | Share the review transaction helper; map constraint violations to the documented codes. |

### Step 13 - Frontend authentication and review pages

| Item | Detail |
|---|---|
| Tests first | `tests/unit/auth-store.spec.ts` (bootstrap, customer register, owner apply, login, logout, status error mapping), `tests/unit/router-guard.spec.ts` (protected redirect, safe return path, role guard, owner placeholder), `tests/unit/register-customer-form.spec.ts`, `tests/unit/register-owner-form.spec.ts` (validation, confirmation, pending outcome, no double submit), `tests/unit/admin-applications.spec.ts` (list, approve, reject, conflict, empty, error), `tests/unit/api-client.spec.ts` (CSRF header, credentials, error envelope). |
| Files | `src/services/api/client.ts`, `src/services/api/auth.ts`, `src/services/api/admin.ts`, `src/stores/auth.ts`, `src/modules/auth/pages/RegisterCustomerPage.vue`, `RegisterOwnerPage.vue`, `LoginPage.vue`, `AccountPage.vue`, `PendingApprovalPage.vue`, `src/modules/owner/pages/OwnerHomePage.vue`, `src/modules/admin/pages/OwnerApplicationsPage.vue`, `src/modules/auth/components/FormField.vue`, `src/router/index.ts`, `src/app/App.vue`, styles |
| Green | Working pages, store, API client, guards, accessible errors, loading and empty states. |
| Refactor | Extract shared form field and error display; no backend business rules duplicated. |

**Frontend flow requirements:**

- On boot: `GET /auth/csrf`, then `GET /auth/me`; store the result.
- API client sends `credentials: 'include'` and `X-CSRF-Token` on POST/PUT/PATCH/DELETE.
- On `401`, clear the user and redirect to login for protected routes.
- On `CSRF_INVALID`, refresh the token and retry once.
- Customer registration success -> `/account`.
- Owner application success -> `/pending-approval` with no authenticated state.
- Login success -> safe `redirect`, else `/admin/owner-applications` for admins, `/owner` for
  owners, `/account` for customers.
- `/admin/owner-applications` requires `admin`; `/owner` requires `salon_owner`.
- `redirect` is accepted only if it starts with `/` and not `//`.

### Step 14 - End-to-end and security verification

| Item | Detail |
|---|---|
| Tests/checks | Browser journey A: customer registers -> account -> refresh -> logout -> login. Browser journey B: owner applies -> pending notice -> admin approves -> owner logs in -> `/owner`. Cookie inspection, CSRF rejection, role denial, open-redirect check, log inspection, OpenAPI inspection. |
| Tooling | E2E tool chosen in F-001 with a small ADR. If not approved, perform both journeys manually and record them; Vitest covers component behavior. |
| Files | `frontend/tests/e2e/auth.spec.ts` (if tool approved), security check notes |

### Step 15 - Documentation and cleanup

| Item | Detail |
|---|---|
| Files | `README.md`, `docs/features/F-001-authentication/PLAN.md`, `Task-List.md`, OpenAPI examples, `.env.example`, administrator bootstrap instructions |
| Checks | Remove dead code, unused dependencies, and temporary test-only routes from production code. Confirm the README explains the two flows and the CLI. |

---

## 4. Database and migration plan

### Migration `0001_authentication`

Creates, in order:

1. `users`
2. `user_roles`
3. `sessions`
4. `owner_applications`

Details:

- UUID primary keys generated in Python (`uuid.uuid4`) to avoid requiring `pgcrypto`.
- `users.email` is `varchar(254)`, not null, unique. The application stores it normalized, so a
  plain unique constraint is sufficient across both flows.
- `users.status` is `varchar(20)` with a check constraint for `pending_approval`, `active`,
  `rejected`, and `suspended`; default `active`. Customer and CLI-created admins are active;
  owner applicants start pending.
- `users.password_hash` is `varchar(255)`.
- `user_roles.role` is `varchar(20)` with a check constraint for `customer`, `salon_owner`, `admin`.
- `user_roles` has a composite primary key and cascades on user deletion.
- `sessions.token_hash` is `char(64)` unique (SHA-256 hex).
- `sessions.user_id` cascades on user deletion and is indexed; `expires_at` is indexed.
- `owner_applications.user_id` is unique and cascades on user deletion.
- `owner_applications.status` is `varchar(20)` with a check constraint for `pending`, `approved`,
  `rejected`.
- `owner_applications.rejection_reason` is `varchar(500)` and required when rejected.
- `owner_applications.reviewed_by` references `users.id` with `on delete set null`.
- `owner_applications.reviewed_at` is required when status is not pending.
- Composite index on `(status, submitted_at)` for the review queue.

### Upgrade and downgrade

- Upgrade: create tables in dependency order.
- Downgrade: drop `owner_applications`, then `sessions`, then `user_roles`, then `users`.
- No backfill is required.
- Downgrade is destructive. It is safe during initial development but must not be run on production
  data without a backup and approval.

### Verification

On a disposable PostgreSQL database:

```text
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

Then run the integration, CLI, and concurrency suites.

### SQLite note

Pure unit tests may use SQLite. Integration, cookie, constraint, CLI, and concurrency tests use
PostgreSQL. No SQLite-specific SQL is allowed in application code.

---

## 5. API and frontend plan

### 5.1 API endpoints

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/v1/auth/csrf` | - | `200 {"csrf_token": "..."}` + cookie | Public |
| `POST` | `/api/v1/auth/register/customer` | `full_name`, `email`, `password` | `201 UserResponse` | Active customer + session; CSRF |
| `POST` | `/api/v1/auth/register/owner` | personal + salon basics | `202 OwnerApplicationAccepted` | Pending; no session; CSRF |
| `POST` | `/api/v1/auth/login` | `email`, `password` | `200 UserResponse` | Status-aware; CSRF |
| `POST` | `/api/v1/auth/logout` | - | `204` | Auth + CSRF |
| `GET` | `/api/v1/auth/me` | - | `200 UserResponse` | Auth |
| `GET` | `/api/v1/admin/owner-applications` | `?status=&limit=&cursor=` | `200 {items, next_cursor}` | Admin |
| `POST` | `/api/v1/admin/owner-applications/{id}/approve` | optional `note` | `200 OwnerApplicationResponse` | Admin + CSRF |
| `POST` | `/api/v1/admin/owner-applications/{id}/reject` | `reason` | `200 OwnerApplicationResponse` | Admin + CSRF |
| `POST` | `/api/v1/admin/users/{user_id}/roles` | `role` | `200 UserResponse` | Admin + CSRF; grant only |

### 5.2 Schemas

- `RegisterCustomerRequest`: `full_name: str`, `email: EmailStr`, `password: str`; `extra="forbid"`.
- `RegisterOwnerRequest`: the customer fields plus `salon_name: str`, `city: str`, `phone: str`,
  `timezone: str`, `currency: str`, `description: str | None`; `extra="forbid"`.
- `LoginRequest`: `email: EmailStr`, `password: str`; `extra="forbid"`.
- `UserResponse`: `id`, `full_name`, `email`, `roles`, `status`, `created_at`.
- `OwnerApplicationAccepted`: `application_id`, `status`, `submitted_at`, `message`.
- `OwnerApplicationResponse`: `id`, `salon_name`, `city`, `phone`, `timezone`, `currency`,
  `description`, `status`, `rejection_reason`, `submitted_at`, `reviewed_at`, `applicant`
  (id, full_name, email, status).
- `RoleGrantRequest`: `role: Literal["admin", "salon_owner"]`.
- `RejectApplicationRequest`: `reason: str`.
- `CsrfResponse`: `csrf_token: str`.
- `ErrorResponse`: stable envelope with `code`, `message`, `fields`, `request_id`.

`EmailStr` requires the `email-validator` package. IANA timezone validation uses the standard
library `zoneinfo`. Currency validation uses a maintained ISO 4217 list or a small explicit
constant, documented in the dependency list.

### 5.3 Status codes and errors

- `201` customer registration.
- `202` owner application accepted.
- `200` login, `/auth/me`, `/auth/csrf`, admin list, approve, reject, role grant.
- `204` logout.
- `401` invalid credentials, unauthenticated session.
- `403` CSRF invalid, forbidden role, pending/rejected/suspended account after correct password.
- `404` unknown application or user.
- `409` duplicate email, application already exists, application already reviewed, user not active.
- `422` validation error, invalid grantable role.
- `500` unexpected error with request id and no internal details.

### 5.4 Cookie and CSRF behavior

- Session cookie: `beautybook_session`, `HttpOnly`, `SameSite=Lax`, `Secure` in production,
  `Path=/`, 7-day max age.
- CSRF cookie: `beautybook_csrf`, not `HttpOnly`, `SameSite=Lax`, `Secure` in production,
  `Path=/`, 7-day max age.
- Owner registration sets no session cookie.
- All POST endpoints require `X-CSRF-Token` equal to the cookie.
- Logout clears both cookies.
- Local development uses the Vite `/api` proxy; no wildcard CORS.

### 5.5 Frontend routes

| Route | Access | Behavior |
|---|---|---|
| `/login` | Public | Redirect authenticated users to their home route; accept a safe `redirect` |
| `/register` | Public | Customer signup; link to the owner flow |
| `/register/owner` | Public | Owner application; link to the customer flow |
| `/pending-approval` | Public | Explains the pending state; no authenticated data |
| `/account` | Authenticated | Show name, email, roles, status, logout |
| `/owner` | `salon_owner` | Placeholder: approval confirmed, salon profile arrives in F-004 |
| `/admin/owner-applications` | `admin` | Review queue with approve/reject |
| `/` | Public | Route by state: admin -> review, owner -> `/owner`, customer -> `/account`, guest -> `/login` |

### 5.6 Frontend state and guards

- Pinia store: `user`, `initialized`, `loading`; getters `isAuthenticated`, `hasRole`; actions
  `bootstrap`, `registerCustomer`, `applyAsOwner`, `login`, `logout`.
- Admin review data is page-local, not global.
- Router guard checks `meta.requiresAuth` and optional `meta.roles`.
- Guard redirects preserve only safe local paths.
- The backend enforces every check; the guard is navigation UX.

### 5.7 Accessibility and UX

- Labels, `autocomplete` (`name`, `email`, `new-password`, `current-password`, `tel`, `address-level2`).
- Inline field errors linked with `aria-describedby`.
- Error summary announced with `aria-live`.
- Focus moves to the first invalid field.
- Submit buttons disabled while pending and show progress text.
- Password visibility toggle with an accessible label.
- Owner application: clear two-section layout and an explicit pending outcome.
- Admin review: destructive rejection requires confirmation and a reason.
- Keyboard-only flow works.
- Mobile-first layout.

---

## 6. Test plan

| Layer | Cases | Tool |
|---|---|---|
| Unit | Email, password, roles, status transitions, application state machine, timezone/currency, safe redirect | pytest |
| Integration | Models/constraints, migration, CSRF, sessions, customer registration, owner application, login status codes, me, logout, role dependency | pytest + PostgreSQL |
| Admin | List, approve, reject, reason validation, audit event, role grant, denial paths | pytest + PostgreSQL |
| CLI | Bootstrap, duplicate refusal, weak password, stdin password, no HTTP route | pytest + PostgreSQL |
| API/contract | Schemas, status codes, no secrets or application data in public responses, unknown fields rejected | pytest + OpenAPI |
| Security | Generic login errors, status only after password, CSRF, mass assignment, non-admin denial, no secrets in `caplog` | pytest |
| Concurrency | Duplicate registration and duplicate approval -> exactly one success | pytest + PostgreSQL |
| Frontend unit | Two forms, store, guards, admin page, API error mapping | Vitest + Vue Test Utils |
| E2E | Customer journey; owner application -> approval -> login -> `/owner` | Tool chosen in F-001; manual fallback |

### Commands to run during implementation

Backend:

```text
python -m pytest tests/unit
python -m pytest tests/integration
python -m pytest tests/concurrency
python -m pytest
ruff check .
ruff format --check .
mypy app
```

Frontend:

```text
npm run test:unit
npm run typecheck
npm run lint
npm run build
```

Database:

```text
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

CI runs the same checks with a PostgreSQL service.

Actual results will be recorded in Section 12 only after they are executed. Do not pre-fill them.

### Test data rules

- Use unique emails per test (UUID suffix) to avoid cross-test coupling.
- Never use real personal data; salon names and cities are fictional.
- Use lower Argon2 cost in tests for speed; keep one production-parameter configuration test.
- Reset the database between integration tests with transactions or a clean schema.
- Admin/owner fixtures for setup may insert roles directly in the database; the approval and grant
  paths themselves must be tested through their real services.
- Assert that no test password appears in captured logs.

---

## 7. Observability and operations

### Logs

- Request id on every request.
- Auth events: `customer_registered`, `owner_application_submitted`, `login_success`,
  `login_failure`, `login_blocked_pending`, `login_blocked_rejected`, `login_blocked_suspended`,
  `logout`, `session_rejected`, `csrf_rejected`.
- Admin events: `owner_application_approved`, `owner_application_rejected`, `role_granted`,
  `admin_bootstrapped`.
- Include outcome, request id, actor id, and application id when known.
- Never log email, phone, password, password hash, session token, CSRF token, or rejection text.
- Log the internal reason for a blocked login, but return only the documented public code.

### Metrics (deferred)

Auth, application, and review counters can be added in F-018. Do not add a metrics stack in F-001
without a concrete operational need.

### Health

- `/health`: process is alive.
- `/ready`: database connection works.
- No secrets or internal details in responses.

### Operations

- The administrator bootstrap command is documented in the README.
- Expired sessions may remain until a cleanup job is added; F-001 can delete expired sessions
  opportunistically on login if simple.
- The review queue has no SLA or notification in F-001; an operator must check it. Email
  notification is F-013.

---

## 8. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Privilege escalation through a role field | Low | Critical | No role field; endpoint selects the flow; `extra="forbid"`; grant requires admin |
| Pending owner gets access early | Medium | High | No session, no role, non-active status rejected on every request |
| Double approval creates duplicate state | Medium | High | Row lock + conditional update + transition tests + concurrency test |
| Administrator created publicly | Low | Critical | No route; CLI only; route-table assertion |
| Non-admin calls review/grant | Medium | High | `require_roles('admin')` on the server, negative tests |
| Owner application data leaks | Medium | High | Admin-only responses; no public listing; no personal data in logs |
| Mass assignment sets `status` | Medium | High | `extra="forbid"` and server-owned transitions |
| Session fixation | Medium | High | New session on login; rotate; reject old cookie for the new session |
| CSRF bypass on admin actions | Medium | High | Double-submit on every state-changing endpoint; constant-time compare; tests |
| Cookie misconfiguration | Medium | High | Centralize flags; test `HttpOnly`/`SameSite`/`Secure` |
| User enumeration | Medium | Medium | Generic login error, dummy hash; status codes only after password |
| Brute force | High | High | Rate limiting deferred to F-003; do not expose publicly until delivered |
| Owner approval becomes a bottleneck | High | Medium | Minimal queue with pagination and oldest-first order; notifications in F-013 |
| Rejected applicant has no path back | High | Medium | Documented support route; re-application in F-004/F-014 |
| Audit only in logs | Medium | Medium | Structured events now; persistent audit table in F-014; no public exposure |
| CLI misuse (password in argv) | Medium | Medium | stdin/prompt only; test asserts no password argument |
| Foundation scope creep | High | Medium | Limit to Section 1; defer CI hardening to F-018 |
| Migration rollback data loss | Medium | High | Downgrade only on disposable databases; document production caution |
| CORS/cookie issues in dev | Medium | Medium | Vite proxy; single browser origin |

---

## 9. Rollout and rollback

### Rollout order

1. Apply the additive Alembic migration.
2. Run the administrator bootstrap command in the target environment.
3. Deploy the backend with auth, registration, and review endpoints.
4. Deploy the frontend with the registration, login, account, owner, and admin review pages.
5. Verify customer registration, owner application, approval, owner login, and role denial.
6. Verify logs contain no secrets or application personal data.

### Configuration

Environment variables (names finalized during implementation):

- `APP_ENV` (`development`, `test`, `production`)
- `DATABASE_URL`
- `SESSION_TTL_DAYS` (default 7)
- `SESSION_COOKIE_SECURE` (derived from `APP_ENV` but overridable in tests)
- `ARGON2_TIME_COST`, `ARGON2_MEMORY_COST`, `ARGON2_PARALLELISM`
- `VITE_API_BASE_URL` (frontend; defaults to `/api/v1` through the Vite proxy)

`.env.example` contains placeholders only. `.env` is gitignored. No administrator credential is
stored in configuration.

### Feature flag

Not required. Authentication is a foundational capability. If a staged rollout is needed, restrict
network access to the environment rather than adding a flag.

### Rollback

- Revert the frontend first if it depends on new endpoints.
- Revert the backend.
- Downgrade the migration only on a disposable database or with a verified backup. The downgrade
  drops all accounts, applications, roles, and sessions.
- Because this is the first authentication release, there is no production user data to preserve
  yet.

### Operational constraint

F-001 must stay internal until F-003 adds rate limiting and email verification, and until F-014
adds persistent audit storage and role revocation.

---

## 10. Documentation updates

- [ ] `Task-List.md`: F-001 status transitions and completion notes.
- [ ] `SPEC.md`: update if behavior changes during implementation.
- [ ] `PLAN.md`: fill Section 12 with actual results.
- [x] ADR-0005: `Accepted` on 2026-11-18.
- [x] ADR-0010: `Accepted` on 2026-11-18.
- [ ] `README.md`: two registration flows, administrator bootstrap, run, test, and environment
  instructions.
- [ ] `docs/ARCHITECTURE.md`: update only if the implemented design differs.
- [ ] `docs/SRS.md`: update traceability if task IDs or product decisions change.
- [ ] OpenAPI: verify endpoints, schemas, and error examples.
- [ ] `.env.example`: document every required variable with placeholders.
- [ ] `docs/features/README.md`: mark F-001 as the current feature.

---

## 11. Completion checklist

- [ ] All acceptance criteria in `SPEC.md` pass.
- [ ] TDD evidence exists for each behavior.
- [ ] Unit tests pass.
- [ ] PostgreSQL integration tests pass.
- [ ] CLI bootstrap tests pass.
- [ ] Registration and approval concurrency tests pass.
- [ ] CSRF and cookie security tests pass.
- [ ] Pending, rejected, and suspended login tests pass.
- [ ] Admin denial tests pass for every admin endpoint.
- [ ] No public admin creation path exists.
- [ ] Frontend tests pass.
- [ ] Both end-to-end journeys verified (or manual verification recorded with the reason).
- [ ] Formatter passes.
- [ ] Linter passes.
- [ ] Type checks pass.
- [ ] `alembic upgrade head`, downgrade, and re-upgrade verified on a disposable database.
- [ ] No password, session token, CSRF token, email, or phone appears in logs or public responses.
- [ ] Migration and rollback notes reviewed.
- [ ] Security/privacy review complete.
- [ ] Documentation and `Task-List.md` updated.
- [ ] Real commands and results recorded in Section 12.
- [ ] Known limitations recorded as follow-up tasks (re-application, role revocation, audit table,
  email notifications).

---

## 12. Completion report

Fill this in only after verification. Never fabricate results.

### Step 7 checkpoint (login and account status), 2026-11-19

- **What changed:** Added `POST /api/v1/auth/login` with Argon2id verification, a dummy
  verification for unknown emails, generic `401 INVALID_CREDENTIALS`, status-specific `403` codes
  only after a correct password, best-effort rehash of outdated hashes, and session rotation of
  the caller's current session. The Vue login page now uses the live endpoint and shows the
  status-aware messages; customer registration was re-verified unchanged.
- **Commands executed and results:** `pytest -q` -> 243 passed, 1 existing `httpx2` deprecation
  warning. `ruff check .` -> clean. `ruff format --check .` -> clean after formatting. `mypy app`
  -> no issues. Frontend `npm run test:unit` -> 19 passed; `npm run typecheck` -> clean;
  `npm run build` -> success. Live browser check against a disposable PostgreSQL database:
  registration `201`, wrong-password login `401`, correct login `200`, and a database query
  showed two sessions for the account with one revoked by rotation. A log scan found no email,
  password, or plaintext token.
- **What was not run and why:** No new Alembic migration was needed, so only the existing `0001`
  upgrade/downgrade path was exercised on the disposable database. Rate limiting, logout,
  `/auth/me`, owner application, and administrator review remain later steps.
- **Known limitations:** Login rate limiting, email verification, and persistent audit storage are
  deferred to F-003/F-014/F-018. The account dashboard and redirect-after-login routing are not
  built yet.
- **Follow-up tasks:** Step 8 was completed on the same date and is recorded below; Step 9
  (logout) and the remaining F-001 steps follow.

### Step 8 checkpoint (current user and role dependency), 2026-11-19

- **What changed:** Added the `CurrentUser` dependency that resolves the session cookie through the
  session service, loads roles from the database on every request, and rejects missing, unknown,
  expired, revoked, and non-active sessions with `401 UNAUTHENTICATED`. Added `GET
  /api/v1/auth/me` returning the safe user shape, and the reusable `require_roles(...)` dependency
  with wiring-time role validation, any-of semantics, and `403 FORBIDDEN` before the handler runs.
- **Commands executed and results:** `pytest -q` -> 259 passed, 1 existing `httpx2` deprecation
  warning. `ruff check .` -> clean. `ruff format --check .` -> 51 files already formatted. `mypy
  app` -> no issues in 23 source files.
- **What was not run and why:** No migration or live-server check was needed; the change adds
  SQLAlchemy reads and HTTP dependencies only, and the PostgreSQL integration tests exercise real
  sessions, expiry, revocation, status changes, and role changes.
- **Known limitations:** Logout, the frontend auth store/bootstrap (`/auth/me` on app load), route
  guards, and the account dashboard remain later steps.
- **Follow-up tasks:** Implement Step 9 (logout) and the remaining F-001 steps.

### Overall feature report

- **What changed:**
- **Commands executed and results:**
- **What was not run and why:**
- **Known limitations:**
- **Follow-up tasks:**
