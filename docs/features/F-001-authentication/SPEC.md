# Feature Specification - F-001 Authentication and Registration Gate

- **Status:** Ready - approved 2026-11-18; implementation in progress
- **Owner:** BeautyBook project owner and engineering agent
- **Task-List entry:** [F-001](../../../Task-List.md)
- **Module(s):** `identity` (temporarily includes user accounts, roles, sessions, and owner
  applications)
- **Related ADRs:** ADR-0010 (registration flows and role assignment, accepted), ADR-0005 (session
  strategy, accepted), ADR-0009 (authorization model), ADR-0002 (PostgreSQL), ADR-0001 (modular
  monolith)
- **Last updated:** 2026-11-18

---

## 1. Problem and objective

BeautyBook has no application code and no user accounts. Every future capability - salon profiles,
owner dashboards, booking, administration - depends on knowing who the user is and what they are
allowed to do.

This feature delivers the first working vertical slice and the **registration gate** for the whole
product:

- a public visitor can register as a **customer** through a dedicated form,
- a public visitor can apply as a **salon owner** through a separate form that collects personal
  and basic salon information,
- the salon-owner account and application stay **pending** until an administrator approves them,
- an approved salon owner can reach the salon dashboard placeholder and will later manage the
  salon, services, images, portfolio, and appointments,
- the **administrator** role is never available through public registration,
- users can log in and log out,
- authenticated and role-guarded routes are protected on the backend and in the frontend,
- passwords are hashed securely, all inputs are validated, and the behavior is covered by tests
  written first.

Because the repository currently has no runnable application, F-001 also includes the **minimum
engineering foundation** required to build and verify this slice: project bootstrap, configuration,
PostgreSQL connection, Alembic baseline, health check, and the test harness. It does not include
the rest of the product.

### Why this is a vertical slice

A vertical slice goes through every layer once - database, backend, API, frontend, tests - using a
small but real feature. The registration gate is a good first slice because it is the entry point
for every actor and it contains the first genuine authorization decision: **who is allowed to
become a salon owner, and who decides?**

### Boundary with later features

| Concern | F-001 | Later |
|---|---|---|
| Customer account | Create, sign in, sign out | Email verification, password reset, profile (F-003) |
| Salon-owner account | Apply, wait, get approved, reach dashboard placeholder | Full salon profile, publish (F-004) |
| Salon data | Basics for the application only (name, city, phone, timezone, currency) | Address, slug, description, services, photos, hours, bookings (F-004+) |
| Administrator | Bootstrap, review applications, grant roles | Full user administration, moderation tools, audit storage (F-014) |
| Authorization | Role dependency and the approval gate | Resource ownership policies (F-002) |

---

## 2. Actors and permissions

| Actor | Allowed | Forbidden |
|---|---|---|
| Public visitor | Register as a customer; apply as a salon owner; log in; request a CSRF token. | Choose a role through a request field; register as an administrator; access protected routes; enumerate users. |
| Prospective salon owner (pending) | Submit one application; read the pending notice after login attempt with correct credentials. | Sign in; receive a session; access any dashboard; hold the `salon_owner` role. |
| Customer | View their own session (`/auth/me`); log out; in later features browse and book. | Access owner/admin routes; read another user's data; assign themselves a role. |
| Salon owner | All customer permissions; after approval, access owner routes for their own salon. | Access administration routes; access another salon's data; manage appointments before approval. |
| Administrator | Review owner applications; approve or reject them; grant `admin` and `salon_owner` roles to active users. | Be created through public registration; approve without an audit record; manage salons or bookings in F-001. |

### Registration flow policy

There are **three separate trust paths**. They are not variants of one form with a role selector.

| Path | Entry point | Account status after submission | Role granted |
|---|---|---|---|
| Customer | `/register` | `active` | `customer` |
| Salon owner | `/register/owner` | `pending_approval` | none (role granted on approval) |
| Administrator | no public entry point | `active` only when provisioned | `admin` |

Rules:

- Each public flow has its own endpoint and schema. The endpoint, not a client field, decides the
  outcome.
- Both public schemas reject unknown fields, including `role`, `id`, `status`, and `is_active`
  (`extra="forbid"`).
- A salon-owner application does **not** create a session and does **not** grant `salon_owner`.
  The role is inserted in the same transaction as administrator approval.
- An email address identifies at most one account across both flows.
- Roles are additive in the data model. An approved owner also keeps the `customer` capability.
- No client can set `status`. Status transitions belong to the server.

See ADR-0010.

### Authentication versus authorization

- **Authentication** answers: "Who are you?" F-001 implements it, including the rule that pending
  and rejected accounts cannot authenticate.
- **Authorization** answers: "What are you allowed to do with this specific resource?" F-001
  provides the reusable role dependency and the approval gate. Full resource-ownership policies for
  salons, services, bookings, and administration are F-002 and later.

---

## 3. User journeys

### 3.1 Customer registration

1. Visitor opens `/register`.
2. Visitor enters full name, email, password, and password confirmation.
3. The frontend performs usability validation and shows inline errors.
4. The frontend sends `POST /api/v1/auth/register/customer` with the CSRF header.
5. The backend validates the input, normalizes the email, checks uniqueness, hashes the password
   with Argon2id, creates an **active** user with the `customer` role, and creates a session.
6. The backend returns `201` with a safe user summary and sets the session and CSRF cookies.
7. The frontend stores the user in Pinia and redirects to `/account` or a safe `redirect` path.
8. The user sees a welcome state with their name and roles.

**Failure paths:**

- Invalid name/email/password: `422`, field-level messages, form input preserved.
- Email already registered: `409 EMAIL_ALREADY_REGISTERED`; offer a login link.
- CSRF missing or wrong: `403 CSRF_INVALID`; the client refreshes the token and retries once.
- Network/server failure: retryable error; never claim the account was created.
- Concurrent duplicate: one request succeeds, the other receives `409`.

### 3.2 Salon-owner application

1. Visitor opens `/register/owner` from the "For salon owners" entry point.
2. Visitor enters personal details (full name, email, password, confirmation) and basic salon
   details (salon name, city, phone, timezone, currency, optional description).
3. The frontend validates the fields and shows the salon timezone/currency choices explicitly.
4. The frontend sends `POST /api/v1/auth/register/owner` with the CSRF header.
5. The backend validates everything, normalizes the email, checks uniqueness, hashes the password,
   and in **one transaction** creates:
   - a user with `status = pending_approval` and the `customer` base role,
   - an `owner_applications` row with `status = pending`.
6. The backend returns `202 Accepted` with the application id, status, and submitted time. It does
   **not** create a session and does **not** set a session cookie.
7. The frontend shows a clear "application received, waiting for administrator approval" screen.
   The applicant is not signed in.
8. The applicant may close the browser. The application remains in the database.

**Failure paths:**

- Invalid personal or salon data: `422` with field-level messages; nothing is created.
- Email already registered (customer or owner): `409 EMAIL_ALREADY_REGISTERED`; explain that an
  account already exists and that applying from an existing account arrives in F-004.
- CSRF failure: `403`; nothing is created.
- Network failure after submission: the UI must not claim success; it offers a retry, and duplicate
  submissions are prevented by the button state and by the unique email constraint.
- Concurrent duplicate: one `202`, one `409`.

**Important:** a pending owner is **not** a salon owner yet. They have no session, no
`salon_owner` role, and no access to any owner route.

### 3.3 Administrator review of owner applications

1. Administrator signs in to an existing administrator account.
2. Administrator opens `/admin/owner-applications`.
3. The page lists pending applications, oldest first, with salon name, city, submitted time, and
   applicant name. Pagination is required.
4. Administrator opens an application and reviews the details.
5. Administrator chooses **Approve** or **Reject**.
   - Approve sends `POST /api/v1/admin/owner-applications/{id}/approve`.
   - Reject sends `POST /api/v1/admin/owner-applications/{id}/reject` with a required reason.
6. Both requests require the CSRF header and an administrator session.
7. The backend locks the application row and performs one atomic transition:
   - **Approve:** application `pending -> approved`, user `pending_approval -> active`,
     `salon_owner` role inserted, `reviewed_by` and `reviewed_at` recorded.
   - **Reject:** application `pending -> rejected`, user `pending_approval -> rejected`,
     `rejection_reason`, `reviewed_by`, `reviewed_at` recorded. No role is inserted.
8. The backend records a structured audit event with the acting administrator, application id, and
   outcome.
9. The list refreshes and the item disappears from the pending filter.

**Failure paths:**

- Non-administrator: `403 FORBIDDEN`; no change.
- Missing or invalid CSRF: `403 CSRF_INVALID`; no change.
- Application already reviewed: `409 APPLICATION_ALREADY_REVIEWED`; no change.
- Two administrators act at the same time: exactly one succeeds; the other receives `409`.
- Approval does not publish the salon. Publishing is F-004.

### 3.4 Approved salon owner

1. Applicant receives approval through the product's support channel. Email notification is
   F-013; F-001 shows the state on the login/pending screen.
2. Applicant opens `/login` and signs in with the same credentials.
3. Login succeeds because the account is now `active`.
4. The account has roles `customer` and `salon_owner`.
5. The frontend redirects to `/owner`, a protected placeholder that confirms approval and explains
   that the salon profile arrives in F-004.
6. `/owner` is guarded by `requiresAuth` and `roles: ['salon_owner']` in the frontend. The backend
   enforcement of owner resources arrives with F-004/F-002.

### 3.5 Login

1. User opens `/login`.
2. User enters email and password.
3. The frontend sends `POST /api/v1/auth/login` with the CSRF header.
4. The backend normalizes the email, looks up the user, verifies the Argon2id hash, and checks the
   account status.
5. If the account is `active`, the backend creates a new session and returns `200` with a safe user
   summary and the session cookie.
6. The frontend loads the user into Pinia and redirects to the intended protected page or the
   default page for that user.

**Failure paths:**

- Unknown email or wrong password: `401 INVALID_CREDENTIALS`, identical response and comparable
  timing. Never reveal which one was wrong.
- Correct password but `pending_approval`: `403 ACCOUNT_PENDING_APPROVAL` with a "still under
  review" message. This is safe because the password was verified, so it does not help an attacker
  discover accounts.
- Correct password but `rejected`: `403 ACCOUNT_REJECTED`.
- Correct password but `suspended`: `403 ACCOUNT_SUSPENDED`.
- Malformed input: `422`.
- CSRF failure: `403 CSRF_INVALID`.
- Too many attempts: not implemented in F-001; see Sections 4 and 9.

### 3.6 Logout

1. Authenticated user clicks "Log out".
2. The frontend sends `POST /api/v1/auth/logout` with the session cookie and CSRF header.
3. The backend marks the current session revoked and clears the session cookie.
4. The frontend clears the Pinia state and redirects to `/login`.
5. A later request with the old cookie returns `401`.

**Failure paths:**

- Session already expired or revoked: the frontend still clears local state.
- CSRF failure: `403`; do not revoke the session.
- Network failure: show an error and keep the user signed in.

### 3.7 Protected and role-guarded routes

1. A route declares `meta.requiresAuth`. The router waits for the auth store's initial
   `/auth/me` check.
2. Unauthenticated users are redirected to `/login?redirect=<safe local path>`.
3. A route may declare `meta.roles`. The frontend guard checks roles for user experience.
4. The backend independently checks the session and roles. A customer calling an administrator
   endpoint receives `403` even if the UI is bypassed.
5. `redirect` is honored only when it is a local path starting with `/` and not `//`.

### 3.8 Administrator provisioning

**First administrator (bootstrap):**

1. An operator with database access runs `python -m app.cli create-admin`.
2. The command prompts for the email, full name, and password (password read without echo, or from
   standard input). The password is never passed as a command-line argument.
3. The command validates and hashes the input and creates an **active** user with the `admin` and
   `customer` roles.
4. The command refuses to continue if the email already exists.

**Later administrators:**

1. An existing administrator signs in.
2. The administrator grants the `admin` role to an existing **active** account through the
   administrator endpoint (in F-001 this is exercised by tests and documented; the full user
   management UI arrives in F-014).
3. The change takes effect on that user's next request.

---

## 4. Scope

### In scope

- Minimal backend bootstrap: configuration, app factory, PostgreSQL session, Alembic baseline,
  `/health` and `/ready`, request ids, test fixtures.
- Minimal frontend bootstrap: Vite + Vue 3 + TypeScript, Vue Router, Pinia, base layout, CSS
  tokens, Vitest setup.
- Tables `users`, `user_roles`, `sessions`, and `owner_applications`.
- Email normalization and uniqueness across both registration flows.
- Password policy and Argon2id hashing.
- Customer registration with auto-login.
- Salon-owner application submission with pending account and pending application.
- Administrator review: list, approve, reject with reason.
- Administrator bootstrap CLI for the first administrator.
- Administrator-only role grant for `admin` and `salon_owner`.
- Login with account-status handling, logout, `/auth/me`, and CSRF token issuance.
- Database-backed session cookie with expiry and revocation.
- CSRF double-submit protection for all state-changing endpoints, including administrator actions.
- Role model and a reusable `require_roles(...)` dependency.
- Frontend pages: customer registration, owner application, pending notice, login, account,
  owner placeholder, minimal admin review.
- Route guards, safe redirect handling, accessible forms and states.
- OpenAPI documentation and unit, integration, security, concurrency, and frontend tests.

### Out of scope

- Full salon profile (address, slug, public page), services, prices, portfolio, hours, and
  publishing (F-004 to F-007).
- Owner dashboard for appointments and salon management (F-011); F-001 ships a placeholder only.
- Resource-level ownership authorization for salons, services, and bookings (F-002).
- Email verification and password reset (F-003).
- Password change, profile editing, avatar, timezone preference (F-003).
- Rate limiting and account lockout (F-003; required before public launch).
- "Sign out everywhere", session management UI, role revocation, last-administrator protection
  enforcement, and persistent audit log (F-014).
- Email notifications for approval or rejection (F-013).
- Re-applying after rejection, and applying as an existing customer (F-004/F-014).
- Reviews, payments, notifications, and booking.
- OAuth/social login, MFA, passkeys.
- Native mobile clients.
- Full CI matrix and production deployment (a minimal CI check is included; hardening is F-018).

### Non-goals

- Building the salon dashboard or salon features in this task.
- Designing the final visual identity.
- Supporting multiple salons per owner in the MVP.

---

## 5. Functional requirements

### 5.1 Customer registration

- **FR-AUTH-001 (Must):** A visitor shall be able to register as a customer with full name, email,
  password, and password confirmation on a dedicated form.
- **FR-AUTH-002 (Must):** The backend shall trim the full name and normalize the email (trim,
  lowercase) before storage and lookup.
- **FR-AUTH-003 (Must):** The backend shall reject a customer registration whose normalized email
  already exists in either flow, with `409 EMAIL_ALREADY_REGISTERED`.
- **FR-AUTH-004 (Must):** Customer registration shall create exactly one user with
  `status = active` and the `customer` role.
- **FR-AUTH-005 (Must):** The customer registration schema shall not accept `role`, `id`,
  `status`, or `is_active`; unknown fields shall be rejected.
- **FR-AUTH-006 (Must):** On success, the backend shall create a session and set the session and
  CSRF cookies, so the customer is signed in immediately.
- **FR-AUTH-007 (Must):** Customer registration shall return `201` with a safe user summary and
  shall never return the password hash, session token, or CSRF secret.
- **FR-AUTH-008 (Must):** User creation, role assignment, and session creation shall be atomic. A
  failure shall leave no partial user or session.

### 5.2 Salon-owner application

- **FR-AUTH-009 (Must):** A visitor shall be able to apply as a salon owner on a dedicated form
  separate from customer registration.
- **FR-AUTH-010 (Must):** The owner application shall require full name, email, password, salon
  name, city, phone, IANA timezone, and ISO 4217 currency. A short description shall be optional.
- **FR-AUTH-011 (Must):** The backend shall validate the timezone against the IANA database and the
  currency against ISO 4217, in addition to the shared name/email/password rules.
- **FR-AUTH-012 (Must):** An owner application shall create exactly one user with
  `status = pending_approval` and the `customer` base role, and exactly one `owner_applications`
  row with `status = pending`.
- **FR-AUTH-013 (Must):** The owner application shall not create a session, shall not set a session
  cookie, and shall not insert the `salon_owner` role.
- **FR-AUTH-014 (Must):** The owner application shall return `202 Accepted` with the application
  id, application status, and submitted time.
- **FR-AUTH-015 (Must):** The owner registration schema shall not accept `role`, `id`, `status`, or
  `is_active`; unknown fields shall be rejected.
- **FR-AUTH-016 (Must):** An email that already belongs to a customer or another owner shall be
  rejected with `409 EMAIL_ALREADY_REGISTERED`, with guidance to sign in.
- **FR-AUTH-017 (Must):** A pending owner shall not be able to authenticate and shall not hold the
  `salon_owner` role.
- **FR-AUTH-018 (Must):** A rejected owner shall not be able to authenticate.
- **FR-AUTH-019 (Must):** Application data shall never be exposed publicly or to another applicant.
- **FR-AUTH-020 (Must):** The database shall enforce at most one owner application per user with a
  unique constraint. F-001 does not support re-application after rejection; applying as an existing
  customer or re-applying is F-004/F-014.

### 5.3 Administrator review

- **FR-AUTH-021 (Must):** An administrator shall be able to list owner applications filtered by
  status, with pagination and a stable order (oldest pending first).
- **FR-AUTH-022 (Must):** An administrator shall be able to approve a pending application.
- **FR-AUTH-023 (Must):** Approval shall be one atomic transition: application `approved`, user
  `active`, `salon_owner` role inserted, `reviewed_by` and `reviewed_at` recorded.
- **FR-AUTH-024 (Must):** An administrator shall be able to reject a pending application with a
  required reason of 1-500 characters.
- **FR-AUTH-025 (Must):** Rejection shall record the reason, set the application to `rejected`, set
  the user to `rejected`, and insert no role.
- **FR-AUTH-026 (Must):** Approve and reject shall only accept an application whose status is
  `pending`; any other state shall return `409 APPLICATION_ALREADY_REVIEWED`.
- **FR-AUTH-027 (Must):** Review endpoints shall require an authenticated administrator. Other
  authenticated users shall receive `403 FORBIDDEN`; unauthenticated requests shall receive `401`.
- **FR-AUTH-028 (Must):** Approve and reject shall require a valid CSRF token.
- **FR-AUTH-029 (Must):** Each review decision shall emit a structured audit event containing the
  acting administrator id, application id, outcome, and request id. It shall not contain the
  applicant's email, phone, or password.
- **FR-AUTH-030 (Must):** Approval shall not publish the salon. Publishing belongs to F-004.
- **FR-AUTH-031 (Must):** Concurrent reviews of the same application shall produce exactly one
  success; the other shall receive `409`.

### 5.4 Administrator provisioning

- **FR-AUTH-032 (Must):** No public endpoint shall create an administrator account or accept
  `admin` as a registration role.
- **FR-AUTH-033 (Must):** A local CLI command shall create the first administrator, usable only by
  an operator with database access.
- **FR-AUTH-034 (Must):** The CLI shall read the password interactively or from standard input,
  never from a command-line argument, and shall never echo or log it.
- **FR-AUTH-035 (Must):** The CLI shall refuse to create an account whose normalized email already
  exists.
- **FR-AUTH-036 (Must):** A CLI-created administrator shall be `active` and hold the `admin` and
  `customer` roles.
- **FR-AUTH-037 (Must):** An authenticated administrator shall be able to grant the `admin` role to
  an existing active user.
- **FR-AUTH-038 (Must):** An authenticated administrator shall be able to grant the `salon_owner`
  role to an existing active user.
- **FR-AUTH-039 (Must):** Role grant shall be idempotent: granting a role the user already holds
  returns success without creating a duplicate.
- **FR-AUTH-040 (Must):** Role grant shall reject `customer` and unknown roles with
  `422 INVALID_ROLE`, and shall reject a non-active target with `409 USER_NOT_ACTIVE`.
- **FR-AUTH-041 (Must):** Only an administrator may grant roles. A customer or owner calling the
  endpoint shall receive `403`, and no user may grant themselves a role through a public route.
- **FR-AUTH-042 (Must):** Role revocation, last-administrator protection, and full user management
  shall be deferred to F-014 and documented as a known gap.

### 5.5 Login, logout, and account status

- **FR-AUTH-043 (Must):** A user shall be able to log in with email and password.
- **FR-AUTH-044 (Must):** Login shall normalize the email exactly as registration does.
- **FR-AUTH-045 (Must):** Login shall verify the Argon2id hash and return `401
  INVALID_CREDENTIALS` for an unknown email or wrong password, with the same public message.
- **FR-AUTH-046 (Must):** Only an `active` account shall receive a session.
- **FR-AUTH-047 (Must):** A pending, rejected, or suspended account shall receive `403` with
  `ACCOUNT_PENDING_APPROVAL`, `ACCOUNT_REJECTED`, or `ACCOUNT_SUSPENDED` respectively. These codes
  shall be returned only after the password has been successfully verified.
- **FR-AUTH-048 (Must):** A successful login shall create a new session. If the request carries an
  existing valid session, that session shall be revoked and replaced; other sessions remain valid.
- **FR-AUTH-049 (Must):** An authenticated user shall be able to log out, which revokes the current
  session and clears the session cookie.
- **FR-AUTH-050 (Must):** Logout shall require a valid session and a valid CSRF token.
- **FR-AUTH-051 (Must):** A user may have multiple active sessions. Logout revokes only the current
  session.

### 5.6 Sessions and protected routes

- **FR-AUTH-052 (Must):** The system shall store only a hash of the session token in the database.
- **FR-AUTH-053 (Must):** A session shall have an absolute expiry and a revocation timestamp.
- **FR-AUTH-054 (Must):** The backend shall reject a missing, invalid, expired, or revoked session
  with `401 UNAUTHENTICATED`.
- **FR-AUTH-055 (Must):** The backend shall reject a session whose user is not `active`.
- **FR-AUTH-056 (Must):** `GET /api/v1/auth/me` shall return id, full name, email, roles, account
  status, and creation time.
- **FR-AUTH-057 (Must):** The system shall provide a reusable dependency that requires one of a set
  of roles and returns `403 FORBIDDEN` when the role is missing.
- **FR-AUTH-058 (Must):** Role and status checks shall be enforced by the backend, not only by
  frontend route guards.
- **FR-AUTH-059 (Must):** Role changes and status changes shall take effect on the next request;
  the session shall not cache roles.

### 5.7 CSRF

- **FR-AUTH-060 (Must):** The system shall issue a random CSRF token in a non-`HttpOnly` cookie and
  return the same token from `GET /api/v1/auth/csrf`.
- **FR-AUTH-061 (Must):** Every state-changing request in F-001 - customer registration, owner
  application, login, logout, approve, reject, and role grant - shall require an `X-CSRF-Token`
  header matching the CSRF cookie.
- **FR-AUTH-062 (Must):** A missing or mismatched token shall return `403 CSRF_INVALID` and shall
  perform no change.
- **FR-AUTH-063 (Must):** CSRF comparison shall use a constant-time comparison.
- **FR-AUTH-064 (Must):** CSRF validation shall happen before any database read or write that could
  reveal or change state.

### 5.8 Input validation

- **FR-AUTH-065 (Must):** Full name shall be 2-100 characters after trimming and shall reject
  control characters. Unicode is allowed.
- **FR-AUTH-066 (Must):** Email shall be a valid address of at most 254 characters.
- **FR-AUTH-067 (Must):** Password shall be 12-128 characters and shall not be entirely
  whitespace. No composition rules (uppercase/symbol) shall be imposed.
- **FR-AUTH-068 (Must):** Salon name shall be 2-120 characters; city 2-100; phone 5-30; description
  at most 1000 characters.
- **FR-AUTH-069 (Must):** Invalid input shall return `422 VALIDATION_ERROR` with field-level
  messages and shall create no user, application, session, or role.
- **FR-AUTH-070 (Must):** A password longer than 128 characters shall be rejected before hashing.
- **FR-AUTH-071 (Must):** The reject-reason field shall be trimmed and required; an empty reason
  shall fail validation.

### 5.9 Security and data handling

- **FR-AUTH-072 (Must):** Passwords shall be hashed with Argon2id using maintained library defaults
  or explicit parameters at least as strong.
- **FR-AUTH-073 (Must):** The system shall never store, log, or return plaintext passwords.
- **FR-AUTH-074 (Must):** Login shall perform a dummy hash verification for unknown emails to
  reduce timing-based account enumeration.
- **FR-AUTH-075 (Must):** If a stored hash uses outdated parameters, the system should rehash after
  a successful login.
- **FR-AUTH-076 (Must):** Session cookies shall be `HttpOnly` and `SameSite=Lax`; `Secure` shall be
  enabled in production.
- **FR-AUTH-077 (Must):** Session tokens shall have at least 256 bits of entropy from a
  cryptographically secure source.
- **FR-AUTH-078 (Must):** Authentication and review logs shall not contain emails, phones,
  passwords, session tokens, or CSRF tokens. They may contain request id, outcome, actor id, and
  application id.
- **FR-AUTH-079 (Must):** The application shall not configure wildcard CORS with credentials. Local
  development uses the Vite proxy so the browser sees one origin.
- **FR-AUTH-080 (Must):** Pending and rejected accounts shall have no usable session, and any
  session belonging to a user who becomes non-active shall be rejected on the next request.
- **FR-AUTH-081 (Must):** The `admin` role shall never be writable from a public registration
  schema, and role writes shall occur only through the CLI or the administrator-only grant
  endpoint.

### 5.10 Frontend

- **FR-AUTH-082 (Must):** The frontend shall provide `/register`, `/register/owner`, `/login`,
  `/account`, `/pending-approval`, `/owner`, and `/admin/owner-applications` using Vue 3,
  TypeScript, and `<script setup>`.
- **FR-AUTH-083 (Must):** The two registration pages shall be visually and semantically distinct,
  with an explicit "I am a customer" / "I am a salon owner" entry choice and no role field.
- **FR-AUTH-084 (Must):** The frontend shall use a typed API client with `credentials: 'include'`,
  JSON requests, CSRF headers, and normalized error mapping for the new error codes.
- **FR-AUTH-085 (Must):** The auth store shall expose `user`, `initialized`, `loading`,
  `isAuthenticated`, `hasRole`, and actions for bootstrap, customer registration, owner
  application, login, and logout.
- **FR-AUTH-086 (Must):** On application start, the frontend shall fetch a CSRF token and call
  `/auth/me`. It shall not store the session token in `localStorage` or `sessionStorage`.
- **FR-AUTH-087 (Must):** `requiresAuth` routes shall redirect unauthenticated users to `/login`
  with a safe local return path.
- **FR-AUTH-088 (Must):** `/admin/owner-applications` shall require the `admin` role and shall show
  loading, empty, error, and paginated list states.
- **FR-AUTH-089 (Must):** `/owner` shall require `requiresAuth` and the `salon_owner` role and
  shall explain that salon management arrives in F-004.
- **FR-AUTH-090 (Must):** The owner application form shall require confirmation before submission,
  show the pending outcome clearly, and never imply that the account is active.
- **FR-AUTH-091 (Must):** Forms shall show loading, validation, server error, and success states,
  disable double submission, and preserve safe input after an error.
- **FR-AUTH-092 (Must):** Forms shall use semantic HTML, labels, appropriate `autocomplete`
  attributes, visible focus, and accessible error messages.
- **FR-AUTH-093 (Must):** The `redirect` query parameter shall be honored only when it is a local
  path starting with `/` and not `//`.
- **FR-AUTH-094 (Must):** The admin review page shall require confirmation for approve and reject
  and shall display the rejection reason field as required.

### 5.11 Foundation required by this feature

- **FR-AUTH-095 (Must):** The backend shall load configuration from environment variables, validate
  it at startup, and fail clearly when required values are missing.
- **FR-AUTH-096 (Must):** The backend shall connect to PostgreSQL and expose `/health` and
  `/ready`, with readiness checking the database.
- **FR-AUTH-097 (Must):** The initial Alembic migration shall create the four tables and shall
  support upgrade and downgrade on a clean PostgreSQL database.
- **FR-AUTH-098 (Must):** The frontend shall build, type-check, and run unit tests.
- **FR-AUTH-099 (Must):** The repository shall include a minimal CI workflow that runs backend and
  frontend checks.
- **FR-AUTH-100 (Must):** The administrator bootstrap command shall be documented in the README
  and shall never be exposed as an HTTP route.

---

## 6. Business rules and invariants

- **BR-AUTH-001:** An email address identifies at most one account, case-insensitively, across both
  registration flows.
- **BR-AUTH-002:** Customer registration creates an active customer and a session.
- **BR-AUTH-003:** Salon-owner registration creates a pending account and a pending application,
  with no session and no `salon_owner` role.
- **BR-AUTH-004:** The `salon_owner` role exists only after administrator approval or an
  administrator grant. The role is proof of review, not of intent.
- **BR-AUTH-005:** No public path creates an administrator. The first administrator comes from the
  CLI; later ones from an existing administrator.
- **BR-AUTH-006:** A user with status `pending_approval`, `rejected`, or `suspended` cannot
  authenticate.
- **BR-AUTH-007:** Approval is atomic and idempotent: one application is reviewed once, and the
  account, role, reviewer, and timestamp change together.
- **BR-AUTH-008:** Rejection requires a reason and never grants a role.
- **BR-AUTH-009:** Only a `pending` application can be approved or rejected.
- **BR-AUTH-010:** Roles are additive. An approved owner also keeps customer capabilities.
- **BR-AUTH-011:** The application never trusts client-provided `id`, `role`, `status`, or
  `is_active`.
- **BR-AUTH-012:** A session is valid only when the token hash exists, `revoked_at` is null, the
  expiry is in the future, and the user is `active`.
- **BR-AUTH-013:** Approval unlocks the dashboard; it does not publish the salon.
- **BR-AUTH-014:** The last administrator cannot be removed. F-001 has no role removal, so this is
  enforced by omission now and by policy in F-014.
- **BR-AUTH-015:** A failed request leaves no partial user, application, role, or session.
- **BR-AUTH-016:** Every privileged review and grant decision is auditable. F-001 emits structured
  audit events; persistent audit storage is F-014.

---

## 7. UX and API behavior

### 7.1 Pages and states

| Page | Purpose | States |
|---|---|---|
| `/register` | Customer signup | idle, validating, submitting, field errors, duplicate email, server error, success |
| `/register/owner` | Salon-owner application | idle, validating, submitting, field errors, duplicate email, server error, submitted/pending |
| `/login` | Sign in | idle, validating, submitting, invalid credentials, pending, rejected, suspended, server error, success |
| `/account` | Minimal protected page | loading, authenticated, session expired, logout pending, logout error |
| `/pending-approval` | Explains the pending state | informational; no session required |
| `/owner` | Approved-owner placeholder | loading, approved, forbidden, session expired |
| `/admin/owner-applications` | Review queue | loading, empty, list, detail, approve/reject pending, conflict, error |

- Mobile-first layout with a centered card on small screens.
- `/register` and `/register/owner` cross-link to each other and state the difference in one
  sentence each.
- The owner form groups "Your details" and "Your salon" and explains that salon details can be
  completed after approval.
- The owner success state says explicitly: "Your account is not active yet. An administrator must
  approve your application."
- Do not reveal whether an email exists on login.
- Show a clear message if cookies are blocked.

### 7.2 API endpoints

| Method | Path | Auth | CSRF | Success | Purpose |
|---|---|---|---|---|---|
| `GET` | `/api/v1/auth/csrf` | Public | No | `200` | Issue/return CSRF token |
| `POST` | `/api/v1/auth/register/customer` | Public | Yes | `201` | Create active customer + session |
| `POST` | `/api/v1/auth/register/owner` | Public | Yes | `202` | Create pending account + application |
| `POST` | `/api/v1/auth/login` | Public | Yes | `200` | Verify credentials + session |
| `POST` | `/api/v1/auth/logout` | Required | Yes | `204` | Revoke current session |
| `GET` | `/api/v1/auth/me` | Required | No | `200` | Return current user |
| `GET` | `/api/v1/admin/owner-applications` | Admin | No | `200` | Paginated application list |
| `POST` | `/api/v1/admin/owner-applications/{id}/approve` | Admin | Yes | `200` | Approve and activate owner |
| `POST` | `/api/v1/admin/owner-applications/{id}/reject` | Admin | Yes | `200` | Reject with reason |
| `POST` | `/api/v1/admin/users/{user_id}/roles` | Admin | Yes | `200` | Grant `admin` or `salon_owner` |

### 7.3 Request examples

```json
POST /api/v1/auth/register/customer
{
  "full_name": "Sara Ahmadi",
  "email": "Sara@Example.com",
  "password": "correct horse battery staple"
}
```

```json
POST /api/v1/auth/register/owner
{
  "full_name": "Neda Karimi",
  "email": "neda@example.com",
  "password": "correct horse battery staple",
  "salon_name": "Rose Hair Studio",
  "city": "Berlin",
  "phone": "+49 30 1234567",
  "timezone": "Europe/Berlin",
  "currency": "EUR",
  "description": "Small studio specializing in color."
}
```

```json
POST /api/v1/admin/owner-applications/3f6c.../reject
{
  "reason": "Salon address could not be verified. Please contact support."
}
```

```json
POST /api/v1/admin/users/8f14.../roles
{
  "role": "admin"
}
```

### 7.4 Response examples

```json
{
  "id": "8f14e45f-ea2f-4c1b-9b7a-1f3c2d4e5f60",
  "full_name": "Sara Ahmadi",
  "email": "sara@example.com",
  "roles": ["customer"],
  "status": "active",
  "created_at": "2026-11-18T10:15:30Z"
}
```

```json
{
  "application_id": "3f6c2a10-7b4e-4c8f-9a11-5d2e7c9b0a44",
  "status": "pending",
  "submitted_at": "2026-11-18T10:20:00Z",
  "message": "Your application is waiting for administrator approval."
}
```

### 7.5 Error codes

| Code | HTTP | Meaning |
|---|---:|---|
| `VALIDATION_ERROR` | 422 | Invalid request body |
| `EMAIL_ALREADY_REGISTERED` | 409 | Email already belongs to an account |
| `APPLICATION_ALREADY_REVIEWED` | 409 | Application is not pending |
| `APPLICATION_NOT_FOUND` | 404 | Unknown application id |
| `USER_NOT_FOUND` | 404 | Unknown user id |
| `USER_NOT_ACTIVE` | 409 | Role grant target is not active |
| `INVALID_ROLE` | 422 | Role cannot be granted through this endpoint |
| `INVALID_CREDENTIALS` | 401 | Unknown email or wrong password |
| `ACCOUNT_PENDING_APPROVAL` | 403 | Correct password, application under review |
| `ACCOUNT_REJECTED` | 403 | Correct password, application rejected |
| `ACCOUNT_SUSPENDED` | 403 | Correct password, account suspended |
| `UNAUTHENTICATED` | 401 | Missing, invalid, expired, or revoked session |
| `FORBIDDEN` | 403 | Authenticated but role or permission not allowed |
| `CSRF_INVALID` | 403 | Missing or mismatched CSRF token |
| `INTERNAL_ERROR` | 500 | Unexpected server error; no internal details |

### 7.6 Cookie contract

| Cookie | HttpOnly | SameSite | Secure | Purpose |
|---|---|---|---|---|
| `beautybook_session` | Yes | Lax | Production only | Opaque session token |
| `beautybook_csrf` | No | Lax | Production only | CSRF double-submit token |

- `Path=/`.
- Session `Max-Age` is 7 days (configurable).
- Owner registration sets **no** session cookie. It may still set/refresh the CSRF cookie.
- Logout clears both cookies with matching attributes.
- The frontend must not read the session cookie.

### 7.7 Validation rules

| Field | Rule |
|---|---|
| `full_name` | Trim; 2-100 characters; reject control characters; Unicode allowed. |
| `email` | Trim; lowercase; valid address; max 254 characters. |
| `password` | 12-128 characters; not entirely whitespace; no forced composition. |
| `salon_name` | Trim; 2-120 characters; control characters rejected. |
| `city` | Trim; 2-100 characters. |
| `phone` | Trim; 5-30 characters; digits, spaces, `+`, `-`, parentheses. |
| `timezone` | Valid IANA identifier, for example `Europe/Berlin`. |
| `currency` | Uppercase ISO 4217 code, for example `EUR`. |
| `description` | Optional; at most 1000 characters. |
| `reason` | Trim; 1-500 characters; required on rejection. |
| Unknown fields | Rejected by the schema (`extra="forbid"`). |

---

## 8. Data impact

### 8.1 Tables

**`users`**

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | Primary key |
| `full_name` | varchar(100) | Not null |
| `email` | varchar(254) | Not null, unique, normalized lowercase |
| `password_hash` | varchar(255) | Not null |
| `status` | varchar(20) | Not null; check in (`pending_approval`, `active`, `rejected`, `suspended`); default `active` |
| `created_at` | timestamptz | Not null, server default now |
| `updated_at` | timestamptz | Not null, server default now |

**`user_roles`**

| Column | Type | Constraints |
|---|---|---|
| `user_id` | UUID | FK `users.id`, on delete cascade |
| `role` | varchar(20) | Check in (`customer`, `salon_owner`, `admin`) |
| - | - | Composite primary key (`user_id`, `role`) |

**`sessions`**

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK `users.id`, on delete cascade, indexed |
| `token_hash` | char(64) | Not null, unique (SHA-256 hex) |
| `expires_at` | timestamptz | Not null, indexed |
| `revoked_at` | timestamptz | Nullable |
| `created_at` | timestamptz | Not null, server default now |

**`owner_applications`**

| Column | Type | Constraints |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK `users.id`, on delete cascade, unique |
| `salon_name` | varchar(120) | Not null |
| `city` | varchar(100) | Not null |
| `phone` | varchar(30) | Not null |
| `timezone` | varchar(64) | Not null |
| `currency` | char(3) | Not null |
| `description` | text | Nullable |
| `status` | varchar(20) | Not null, default `pending`; check in (`pending`, `approved`, `rejected`) |
| `rejection_reason` | varchar(500) | Nullable; required when `status = rejected` |
| `reviewed_by` | UUID | FK `users.id`, on delete set null, nullable |
| `submitted_at` | timestamptz | Not null, server default now |
| `reviewed_at` | timestamptz | Nullable; required when status is not `pending` |
| `created_at` | timestamptz | Not null, server default now |
| `updated_at` | timestamptz | Not null, server default now |

### 8.2 Indexes and constraints

- Unique index on `users.email` (normalized).
- Composite primary key on `user_roles`.
- Unique index on `sessions.token_hash`.
- Index on `sessions(user_id)` and `sessions(expires_at)`.
- Unique index on `owner_applications.user_id` (one application per account in the MVP).
- Index on `owner_applications(status, submitted_at)` for the review queue.
- Check constraint on `users.status`.
- Check constraint on `user_roles.role`.
- Check constraint on `owner_applications.status`.
- Check constraint: `status = 'rejected'` implies `rejection_reason IS NOT NULL`.
- Check constraint: `status <> 'pending'` implies `reviewed_at IS NOT NULL`.
- No email-verification column in F-001; it is added in F-003.
- No salon table in F-001; the application is a gate record, not the salon.

### 8.3 Migration

- One initial Alembic migration creates `users`, `user_roles`, `sessions`, and
  `owner_applications`.
- Downgrade drops `owner_applications`, `sessions`, `user_roles`, then `users`.
- No backfill.
- The migration must run on PostgreSQL and be reviewed manually.
- SQLite may run the migration for portable tests, but PostgreSQL is authoritative.
- The migration must be re-runnable in the documented upgrade -> downgrade -> upgrade order.

### 8.4 Personal data and retention

- Stored personal data: full name, email, password hash, phone, city, salon name, optional
  description, session token hash, reviewer identity, rejection reason.
- Session token plaintext exists only in the browser cookie and briefly in request memory.
- Owner applications are business records; they are not deleted when a user is rejected in F-001.
  Retention policy is F-018.
- Expired/revoked session rows may be deleted by a periodic cleanup job (F-003/F-018).
- Account deletion and export are out of scope for F-001.
- Application data must never appear in public API responses, logs, or analytics.

---

## 9. Security and privacy

### 9.1 Registration gate

- The gate is enforced in data and in the service layer, not only in the UI:
  - pending/rejected users have no session,
  - the `salon_owner` role does not exist before approval,
  - the review endpoints require `admin`,
  - approval and role insertion share one transaction.
- There is no "role" parameter anywhere in a public schema. The endpoint selects the flow.
- An attacker who learns an email cannot distinguish a pending owner from an unknown account
  without the password.

### 9.2 Administrator protection

- No public admin registration. The first admin is created by an operator-run CLI.
- The CLI is not mounted in the HTTP app and is not callable through the API.
- The admin grant endpoint is protected by `require_roles('admin')` and requires CSRF.
- Every review and grant emits an audit event with the actor id.
- Full audit persistence, revocation, and last-admin enforcement are F-014; until then, F-001 must
  not be exposed publicly.

### 9.3 Password handling

- Argon2id via a maintained library (`argon2-cffi` recommended).
- Production parameters: at least `time_cost=3`, `memory_cost=65536 KiB`, `parallelism=4`.
- Test settings may use lower cost for speed, but production defaults must be asserted by a
  configuration test.
- Password length is capped at 128 before hashing.
- Passwords are never logged, returned, or included in error details.
- Rehash on login if the stored hash uses weaker parameters (best effort).

### 9.4 Session handling

- Tokens from `secrets.token_urlsafe(32)` (at least 256 bits of entropy).
- Store SHA-256 of the token, not the token itself.
- Absolute 7-day expiry; logout revokes immediately.
- Rotate on login to prevent session fixation.
- Reject expired, revoked, or non-active-user sessions on every protected request.
- Multiple sessions per user are allowed; current-session logout only.

### 9.5 CSRF

- Double-submit cookie: random token in `beautybook_csrf`, echoed in `X-CSRF-Token`.
- Required on both registrations, login, logout, approve, reject, and role grant.
- Constant-time comparison.
- `SameSite=Lax` adds defense in depth.
- Local development uses the Vite proxy so there is one browser origin.

### 9.6 Account enumeration

- Login uses one generic message for unknown email and wrong password, with comparable timing.
- A dummy Argon2 verification runs for unknown emails.
- Status-specific codes are returned only after the password is verified.
- Registration necessarily reveals that an email is taken (`409`). This is an accepted usability
  trade-off; rate limiting in F-003 reduces abuse.

### 9.7 Deferred security controls

The following are **not** in F-001 and are tracked in F-003/F-014/F-018:

- login/register rate limiting and account lockout,
- email verification,
- password reset,
- password change and "sign out everywhere",
- breach-password list checks,
- MFA/passkeys,
- role revocation and last-administrator enforcement,
- persistent audit log storage and review UI,
- production secret management and key rotation.

**Operational constraint:** F-001 must not be exposed on the public internet until rate limiting,
email verification, and persistent audit storage are delivered.

### 9.8 Privacy

- Do not log emails, phones, passwords, or tokens.
- Do not include personal data in analytics events.
- Return only the minimum fields required by each screen.
- An applicant can see only their own pending notice; the API returns application data only to
  administrators.
- The API never returns another user's data.

---

## 10. Edge cases

- Email with uppercase letters or leading/trailing spaces, in either flow.
- Names with Unicode, apostrophes, or hyphens.
- Password exactly at 12 and 128 characters; 11 and 129 rejected.
- Password containing spaces but not entirely whitespace.
- Customer registers with an email that belongs to a pending owner, and the reverse.
- Two simultaneous customer registrations for the same email.
- Two simultaneous owner applications for the same email.
- Owner proposes an invalid timezone (`Mars/Olympus`) or a lowercase/invalid currency.
- Pending owner tries to log in before approval.
- Rejected owner tries to log in after rejection.
- An owner is approved while their login attempt is in flight.
- Administrator approves twice; two administrators approve concurrently.
- Administrator rejects without a reason; reason is whitespace; reason is 501 characters.
- Administrator tries to approve a rejected application.
- Administrator grants `admin` to a pending or rejected user.
- Administrator grants a role the user already has.
- Administrator grants `customer` or an unknown role.
- Customer calls any administrator endpoint.
- Administrator calls the endpoint without a CSRF token.
- The only administrator tries to demote themselves (no removal endpoint in F-001; must be
  impossible, not merely hidden).
- CLI run with an existing email; CLI run with a weak password.
- Bootstrap run twice.
- Session expired, revoked, malformed, or belonging to a user who just became suspended.
- Missing CSRF cookie, missing header, mismatched header, reused old token.
- Login while already authenticated: create a new session, replace the cookie.
- Logout twice: second request returns `401`; UI still clears state.
- `/auth/me` after logout: `401`.
- Browser blocks cookies: login appears successful but `/auth/me` fails; UI explains.
- Network failure during owner submission: do not assume success; retry is safe because the unique
  email constraint prevents a duplicate account.
- Open redirect via `?redirect=https://evil.example` or `//evil.example`.
- Very long email, password, salon name, or description.
- Multiple tabs: logout in one tab invalidates the session in another on the next request.
- Server restart: sessions remain valid because they are in PostgreSQL.

---

## 11. Acceptance criteria

### AC-1 - Customer registration succeeds

**Given** a visitor provides a valid name, unique email, and valid password  
**When** they submit `/auth/register/customer` with a valid CSRF token  
**Then** the API returns `201`, the body contains the user with role `customer` and
`status: active`, no password hash appears, and session and CSRF cookies are set.

### AC-2 - Customer registration duplicate email

**Given** an account already exists for `sara@example.com`  
**When** a visitor registers with `SARA@example.com`  
**Then** the API returns `409 EMAIL_ALREADY_REGISTERED` and no second user is created.

### AC-3 - Owner application is pending

**Given** a visitor provides valid personal and salon details with a unique email  
**When** they submit `/auth/register/owner` with a valid CSRF token  
**Then** the API returns `202`, creates a user with `status: pending_approval`, creates a pending
`owner_applications` row, sets no session cookie, and grants no `salon_owner` role.

### AC-4 - Pending owner cannot sign in

**Given** a pending owner with a correct password  
**When** they attempt login  
**Then** the API returns `403 ACCOUNT_PENDING_APPROVAL`, creates no session, and the account and
application are unchanged.

### AC-5 - Approval activates the owner

**Given** an administrator and a pending application  
**When** the administrator approves it with a valid CSRF token  
**Then** the API returns `200`, the application becomes `approved`, the user becomes `active`, the
`salon_owner` role exists, `reviewed_by`/`reviewed_at` are set, and the owner can log in.

### AC-6 - Rejection blocks the owner

**Given** an administrator and a pending application  
**When** the administrator rejects it with a reason  
**Then** the application becomes `rejected` with the reason, the user becomes `rejected`, no
`salon_owner` role exists, and login returns `403 ACCOUNT_REJECTED`.

### AC-7 - Review is single-use

**Given** an application that is already approved or rejected  
**When** an administrator tries to review it again  
**Then** the API returns `409 APPLICATION_ALREADY_REVIEWED` and no state changes.

### AC-8 - Concurrent review

**Given** two administrators reviewing the same pending application at the same time  
**When** both requests arrive  
**Then** exactly one succeeds and the other receives `409`; exactly one role row and one reviewer
are recorded.

### AC-9 - Administrator endpoints are protected

**Given** an authenticated customer or salon owner  
**When** they call any `/api/v1/admin/*` endpoint  
**Then** the API returns `403 FORBIDDEN`.  
**Given** no session, the API returns `401`.  
**Given** an administrator, the request is allowed.

### AC-10 - Administrator cannot be registered publicly

**Given** a customer or owner registration request containing `"role": "admin"`  
**When** it is submitted  
**Then** the request is rejected by schema validation and no administrator is created.  
**And** no public endpoint exists that creates an administrator account.

### AC-11 - First administrator bootstrap

**Given** a clean database and an operator  
**When** the CLI `create-admin` runs with a unique email and a valid password  
**Then** an active user with the `admin` and `customer` roles exists, and running it again with the
same email fails without changing data.

### AC-12 - Administrator grant

**Given** an administrator and an active customer  
**When** the administrator grants the `admin` role with a valid CSRF token  
**Then** the customer receives the role and the change applies on their next request.  
**Given** a non-active target, the API returns `409 USER_NOT_ACTIVE`.  
**Given** a duplicate grant, the API succeeds without a duplicate row.

### AC-13 - Non-administrator cannot grant roles

**Given** an authenticated customer  
**When** they call the role-grant endpoint  
**Then** the API returns `403` and no role is added.

### AC-14 - Validation

**Given** an invalid email, a password shorter than 12 characters, an invalid timezone, or an
invalid currency  
**When** the visitor submits either registration form  
**Then** the API returns `422 VALIDATION_ERROR` with a field-level message and creates no user,
application, role, or session.

### AC-15 - CSRF protection

**Given** any state-changing F-001 request without the `X-CSRF-Token` header  
**When** it is submitted  
**Then** the API returns `403 CSRF_INVALID` and performs no database change.

### AC-16 - Password security

**Given** a completed customer registration or owner application  
**When** the stored user is inspected  
**Then** `password_hash` starts with an Argon2id identifier and is not the plaintext password.

### AC-17 - Email normalization

**Given** an email with uppercase letters and surrounding spaces in either flow  
**When** the user submits  
**Then** the stored and returned email is trimmed and lowercase, and login works with any case.

### AC-18 - Logout revokes the session

**Given** an authenticated active user  
**When** they log out with a valid CSRF token  
**Then** the API returns `204`, the session row is revoked, and the old cookie cannot access
`/auth/me`.

### AC-19 - Session rules

**Given** no session, an expired session, a revoked session, or a session for a user who is no
longer active  
**When** a protected route is called  
**Then** the API returns `401 UNAUTHENTICATED`.

### AC-20 - Owner dashboard gate

**Given** an approved owner signed in  
**When** they open `/owner`  
**Then** the page renders.  
**Given** a customer, the frontend guard redirects them to `/account`.  
**Given** a pending owner, they cannot sign in at all.

### AC-21 - Frontend journeys

**Given** the frontend is running  
**When** a visitor registers as a customer, refreshes, and logs out  
**Then** the session is restored after refresh and logout returns them to `/login`.  
**When** a visitor applies as an owner, they see the pending notice and are not signed in.  
**When** an administrator approves the application, the owner can log in and reach `/owner`.

### AC-22 - Open redirect blocked

**Given** `/login?redirect=https://evil.example`  
**When** login succeeds  
**Then** the frontend redirects to `/account` or `/owner`, not the external site.

### AC-23 - Tests and migration

**Given** a clean PostgreSQL database  
**When** the migration is upgraded and the backend tests run  
**Then** the migration succeeds and all F-001 tests pass. The migration downgrade also succeeds on
a disposable database.

---

## 12. Test strategy

| Layer | What will be tested | Tool |
|---|---|---|
| Unit | Email normalization, password policy, role policy, status transitions, application state machine, timezone/currency validation, safe redirect | pytest |
| Integration | Customer registration, owner application, duplicate email across flows, login status codes, logout, `/auth/me`, CSRF, cookies, session rotation, role dependency | pytest + PostgreSQL |
| Admin | List/approve/reject, atomic activation, audit event, role grant, non-admin denial | pytest + PostgreSQL |
| CLI | Bootstrap admin, duplicate email refusal, password never in argv, idempotent behavior | pytest + PostgreSQL |
| API/contract | Request/response schemas, status codes, no password hash or application data in public responses | pytest + OpenAPI |
| Security | Generic login errors, status codes only after password verification, CSRF rejection, mass-assignment rejection, no secrets in logs | pytest |
| Concurrency | Duplicate registration and duplicate approval races | pytest + PostgreSQL |
| Frontend unit | Two registration forms, auth store, router guards, admin review states, API error mapping | Vitest + Vue Test Utils |
| E2E | Customer journey and owner application -> approval -> login -> `/owner` | Tool chosen in F-001 (ADR required) |

### Test-first order

1. Email, password, role, status, and application-state unit tests.
2. Database model, constraint, and migration tests.
3. CSRF dependency tests.
4. Session service tests.
5. Customer registration integration tests.
6. Owner application integration tests.
7. Login and account-status integration tests.
8. `/auth/me` and role-dependency tests.
9. Administrator bootstrap CLI tests.
10. Administrator role-grant tests.
11. Administrator review and concurrency tests.
12. Frontend store, form, and guard tests.
13. End-to-end journeys.

SQLite may be used for pure unit tests. Integration, security, concurrency, and migration tests run
on PostgreSQL.

---

## 13. Dependencies and open questions

### Dependencies

- F-000 documentation baseline is complete.
- PostgreSQL is available for development and tests.
- ADR-0010 (registration flows and role assignment) is accepted (2026-11-18).
- ADR-0005 (session strategy) is accepted (2026-11-18).
- Python 3.12+, Node.js 20+, and the tooling chosen during bootstrap.
- An IANA timezone database and an ISO 4217 currency list available to the backend.

### Resolved decisions for F-001

| Decision | Resolution | Rationale |
|---|---|---|
| Registration flows | Two separate public flows | Different trust levels and different data (ADR-0010). |
| Salon-owner role timing | Granted at approval, not at registration | The role becomes proof of review. |
| Pending account login | Denied entirely | A pending account must have no usable access. |
| Owner application data | Basics only (name, city, phone, timezone, currency) | The full salon profile is F-004. |
| Approval unlocks | Dashboard placeholder only | Publishing must remain a deliberate F-004 action. |
| First administrator | Local CLI command | No public path and no secret URL. |
| Later administrators | Administrator-only role grant | Satisfies "only an authorized administrator". |
| Role revocation | Deferred to F-014 | Keeps F-001 focused; documented gap. |
| Session mechanism | Database-backed HttpOnly cookie | Simple revocation, safer than localStorage tokens (ADR-0005). |
| Session lifetime | 7 days absolute | Simple, configurable, reasonable for a marketplace. |
| CSRF | Double-submit for all state-changing requests | Protects login CSRF and authenticated writes. |
| Password policy | 12-128 characters, no composition rules | Length is the strongest practical factor. |
| Email verification | Deferred to F-003 | No sensitive actions yet; tracked before launch. |
| Rate limiting | Deferred to F-003 | Needs a shared store decision; F-001 must not be public until then. |
| Resource ownership checks | Deferred to F-002 | F-001 provides roles and the approval gate. |

### Open questions

None block F-001. The following are explicitly deferred and tracked:

- Production administrator provisioning runbook and secret handling (F-018).
- Whether email verification is required before login or only before sensitive actions (F-003).
- Production rate-limit store and thresholds (F-003/F-018).
- E2E tool selection and ADR (before E2E implementation).
- How an existing customer applies to become an owner (F-004).
- How a rejected applicant re-applies (F-004/F-014).
- Notification of approval/rejection by email (F-013).
- Launch market, default currency, and language (still open in the SRS).

---

## 14. Decision log

| Decision | Options considered | Chosen | Rationale | ADR |
|---|---|---|---|---|
| Registration model | One form with role selector, customer-only then upgrade, two flows | Two explicit flows | Different trust levels and data; no self-assigned role | ADR-0010 |
| Owner activation | Immediate role, UI-only gate, admin approval | Admin approval, role at approval | Role proves review; gate enforced in data | ADR-0010 |
| Admin creation | Public admin signup, secret URL, env variable, CLI + admin grant | CLI bootstrap + admin-only grant | No public path, auditable, no committed secret | ADR-0010 |
| Session strategy | JWT in localStorage, refresh tokens, DB sessions | DB-backed cookie sessions | Revocable, not JavaScript-readable | ADR-0005 |
| Role storage | Single role column, join table, policy engine | `user_roles` join table + checks | Supports additive roles | ADR-0009 |
| Password hash | bcrypt, scrypt, Argon2id | Argon2id | Modern memory-hard hashing | This SPEC |
| CSRF | None, SameSite only, double-submit | Double-submit + SameSite | Simple, testable, protects auth POSTs | This SPEC |
| Audit in F-001 | Table now, logs only, skip | Structured logs now, table in F-014 | Avoids a half-built audit feature; gap documented | This SPEC |

---

## 15. Definition of Ready

- [x] Task registered in `Task-List.md` (status `Ready`).
- [x] Actors, permissions, and the three registration paths defined.
- [x] User journeys and failure paths defined for both public flows and approval.
- [x] In-scope and out-of-scope items explicit.
- [x] Acceptance criteria are measurable.
- [x] Data, API, security, and privacy impact identified.
- [x] ADR-0005 and ADR-0010 are accepted (2026-11-18).
- [x] Test strategy defined, including PostgreSQL, CLI, and concurrency.
- [x] SPEC and PLAN approved by the project owner (2026-11-18).
- [x] Task moved to `Ready`.

**Implementation proceeds in the order defined in `PLAN.md`.**
