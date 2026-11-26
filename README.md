# BeautyBook

**An online marketplace for beauty salons and hair salons.**

BeautyBook lets customers discover salons, compare services and prices, see real appointment
availability, and book online. Salon owners get a public profile, a service catalogue, working
hours, a photo portfolio, and a booking dashboard. Administrators keep the platform safe and
operational.

> **Current status: F-001 in progress.**
> The application foundation runs: backend configuration, request IDs, error envelope, database
> engine, `/health` and `/ready`, the Vue/Vite shell, `.env.example`, Compose file, and CI.
> The first feature, **F-001 Authentication and Registration Gate**, is `In Progress`; ADR-0005
> and ADR-0010 are accepted and implementation follows the TDD order in the feature PLAN.
> Customer registration and login are implemented end to end. `POST /api/v1/auth/register/customer`
> creates an active customer, hashes the password with Argon2id, assigns the `customer` role, and
> starts a session in one atomic transaction. `POST /api/v1/auth/login` verifies the Argon2id hash,
> returns one generic `401` for an unknown email or wrong password, returns status-specific `403`
> codes only after a correct password, rotates the current session, and issues a new `HttpOnly`
> session cookie. `GET /api/v1/auth/me` resolves the session on every request and returns the
> current user with database-backed roles, and `require_roles(...)` provides the reusable
> deny-by-default role gate. The Vue frontend includes working registration and login screens, a
> typed API client with CSRF handling, loading/error states, and accessible forms. Owner
> application, administrator review, logout, the account dashboard, and the remaining screens are
> still pending.
> The design has two separate public registration flows: customers and salon owners. Salon-owner
> accounts require administrator approval; administrator accounts are never public.

---

## 1. What the product will do

### Customers

- Register, log in, and manage their account.
- Browse and search published salons.
- View a salon's description, address, contact details, photos, services, prices, and working
  hours.
- Compare services and prices between salons.
- View available appointment slots in a clearly stated timezone.
- Book an appointment online.
- View, cancel, and manage their own bookings.

### Salon owners

- Apply through a dedicated salon-owner registration form with personal and basic salon details.
- Wait for administrator approval before the account becomes active.
- After approval, complete the salon profile and manage the public page.
- Add, update, deactivate, and remove services.
- Manage service durations, prices, and optional buffers.
- Upload a cover photo and portfolio images.
- Define weekly working hours and unavailable periods.
- View and manage the salon's appointments.

### Administrators

- Are created only out-of-band or by an existing administrator; there is no public admin signup.
- Review and approve or reject salon-owner applications.
- Manage users and salon accounts.
- Review, approve, suspend, or reactivate salons.
- Configure platform-wide settings and service categories.
- Inspect bookings for support purposes.
- Review an audit trail of privileged actions.

Customer reviews are **planned for a future phase** and are not part of the first usable release.

---

## 2. Technology stack

| Area | Choice | Why |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Vite | Modern, fast, and a good fit for a single-page marketplace UI. |
| Routing | Vue Router | Standard routing for Vue applications. |
| Client state | Pinia | Shared state only (for example, the signed-in user), not a copy of all server data. |
| Styling | Modern plain CSS with design tokens | Responsive CSS Grid/Flexbox plus CSS custom properties; no extra UI framework is required for the first release. |
| Backend | Python + FastAPI | Typed, fast, and generates OpenAPI documentation automatically. |
| Validation | Pydantic | Explicit request and response contracts. |
| ORM | SQLAlchemy 2.x | Typed database mappings and explicit transactions. |
| Migrations | Alembic | Every schema change is versioned and reviewable. |
| Database | PostgreSQL | The main application database, including local development and integration tests. |
| Lightweight tests | SQLite | Only for fast, portable unit-level tests. Never used in production. |
| Backend tests | pytest | Unit, integration, API, security, and concurrency tests. |
| Frontend tests | Vitest (+ Vue Test Utils) | Component and composable tests. |
| End-to-end tests | Planned; tool chosen in F-001 | Critical customer, owner, and admin browser journeys. |
| API style | REST under `/api/v1` | Simple, explicit, and documented through OpenAPI. |

No additional major technology should be added without an ADR that explains the reason, the
alternatives, and the trade-offs.

---

## 3. Repository map

```text
BeautyBook/
├── AGENTS.md                  # Mandatory rules for AI agents and contributors
├── README.md                  # This file
├── Task-List.md               # The single delivery queue and feature-intake gate
├── .gitignore
├── backend/                   # FastAPI application (skeleton only for now)
│   ├── README.md
│   ├── app/
│   │   ├── api/v1/            # Versioned HTTP routers
│   │   ├── core/              # Cross-cutting configuration, security, logging
│   │   ├── modules/           # Domain modules
│   │   │   ├── identity/
│   │   │   ├── users/
│   │   │   ├── salons/
│   │   │   ├── services/
│   │   │   ├── portfolio/
│   │   │   ├── availability/
│   │   │   ├── bookings/
│   │   │   ├── notifications/
│   │   │   └── administration/
│   │   └── infrastructure/    # Database, email, storage, and other adapters
│   ├── migrations/            # Alembic migrations
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── concurrency/
├── frontend/                  # Vue 3 application (skeleton only for now)
│   ├── README.md
│   ├── src/
│   │   ├── app/
│   │   ├── router/
│   │   ├── modules/
│   │   │   ├── auth/
│   │   │   ├── salons/
│   │   │   ├── services/
│   │   │   ├── booking/
│   │   │   ├── customer-dashboard/
│   │   │   ├── owner-dashboard/
│   │   │   └── admin/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── services/api/
│   │   ├── stores/
│   │   └── assets/styles/
│   └── tests/
│       ├── unit/
│       └── e2e/
├── docs/
│   ├── ARCHITECTURE.md        # System architecture and technical design
│   ├── SRS.md                 # Software requirements specification
│   ├── ROADMAP.md             # Phases, milestones, and release gates
│   ├── adr/                   # Architecture Decision Records
│   │   ├── README.md
│   │   ├── 0001-modular-monolith.md
│   │   ├── 0002-database-strategy.md
│   │   ├── 0003-booking-concurrency.md
│   │   ├── 0004-timezone-model.md
│   │   ├── 0005-authentication-session-strategy.md
│   │   ├── 0006-image-storage.md
│   │   ├── 0007-frontend-styling.md
│   │   ├── 0008-money-representation.md
│   │   ├── 0009-authorization-model.md
│   │   └── 0010-role-assignment.md
│   ├── features/              # One folder per feature, created during intake
│   │   ├── README.md
│   │   └── F-001-authentication/
│   │       ├── SPEC.md
│   │       └── PLAN.md
│   └── templates/
│       ├── SPEC-TEMPLATE.md
│       ├── PLAN-TEMPLATE.md
│       └── ADR-TEMPLATE.md
├── infra/                     # Deployment and local infrastructure notes
│   └── README.md
└── .github/workflows/         # CI pipelines (added in F-001)
```

The folders currently contain `.gitkeep` placeholders so the intended structure is visible. No
application logic has been written.

> `scheduling-blueprint-1/` is the original generic scheduling blueprint that was present before
> this project started. It is preserved as reference material and is **not** part of the
> BeautyBook application. You may archive or remove it later once you no longer need it.

---

## 4. Documentation guide

Read these in order:

1. **`AGENTS.md`** - how work must be planned, implemented, tested, and reported.
2. **`docs/SRS.md`** - what the product must do, for whom, and why.
3. **`docs/ARCHITECTURE.md`** - how the system is structured and where the hard problems live.
4. **`docs/ROADMAP.md`** - the order in which the product will be built.
5. **`Task-List.md`** - the current backlog and task statuses.
6. **`docs/adr/`** - the important technical decisions and their trade-offs.

Feature-specific documents live in:

```text
docs/features/<TASK-ID>-<short-name>/
├── SPEC.md
└── PLAN.md
```

They are created only when the feature enters the intake process. Do not create empty ones just
to "have the file".

---

## 5. The non-negotiable workflow

For every feature:

1. Understand the request and ask about ambiguities.
2. Register the feature in `Task-List.md`.
3. Write `SPEC.md`.
4. Define measurable acceptance criteria.
5. Write `PLAN.md`.
6. Identify dependencies and risks.
7. Decide whether an ADR is needed.
8. Write failing tests first.
9. Implement the smallest correct change.
10. Run the tests and record the real results.
11. Update the documentation.
12. Mark the task Done only after verification.

This is Red -> Green -> Refactor, wrapped in a documentation gate. It is deliberately a little
slower at the start and much safer later.

---

## 6. Key design decisions in plain language

### Modular monolith

The backend is one application, but its code is divided into modules such as `salons`, `bookings`,
and `availability`. Each module owns its rules and data access. This is much easier to run and
debug than many small services, while still keeping the code organized. If the project ever grows
enough to need separate services, the module boundaries make that easier. See
`docs/adr/0001-modular-monolith.md`.

### PostgreSQL for the main database

PostgreSQL is used for development, integration tests, and production. This avoids a common trap:
a feature works on a lightweight local database but behaves differently in production. SQLite is
allowed only for fast tests that do not depend on PostgreSQL-specific behavior. See
`docs/adr/0002-database-strategy.md`.

### UTC for instants, IANA timezones for schedules

An appointment is a moment in time, so it is stored in UTC. A salon's working hours are local
wall-clock rules, so the salon stores an IANA timezone such as `Europe/Berlin`. This distinction
prevents bugs when customers and salons are in different timezones or when daylight saving
changes. See `docs/adr/0004-timezone-model.md`.

### Database-level double-booking protection

Checking "is this slot free?" in Python and then inserting a row is not safe: two requests can
both pass the check at the same time. The final protection must be enforced by PostgreSQL, using
an exclusion constraint over the salon and the occupied time interval. See
`docs/adr/0003-booking-concurrency.md`.

### Money as integers

Prices are stored as integer minor units (for example, cents) plus a currency code. Floating-point
numbers cannot represent every decimal amount exactly, which is unacceptable for prices.

### Three roles, three trust paths

BeautyBook does not use a role selector at signup. Each role has its own path:

- **Customer:** `/register` creates an active customer account immediately.
- **Salon owner:** `/register/owner` creates a pending account and a pending salon application. The
  account and application stay pending until an administrator approves them. Only then is the
  salon-owner role granted and dashboard access unlocked. Approval does not publish the salon.
- **Administrator:** there is no public admin registration. The first administrator is created by a
  local operational command; later administrators are assigned by an existing administrator.

This prevents someone from signing up as an owner or an admin. See
`docs/adr/0010-role-assignment.md`.

---

## 7. Getting started

The F-001 foundation runs. Customer registration (`/register`) and login (`/login`) are connected
to the backend and work end to end, and the backend exposes `GET /api/v1/auth/me` for the current
user. Both authentication screens are Persian and right to left (F-019). Owner application, the
account dashboard, logout, and the administrator screens are still being implemented.

### Prerequisites

- Python 3.12 or newer (3.14 was used locally).
- Node.js 20 or newer and npm (Node 26.13.1 and npm 11.20.0 were used locally).
- PostgreSQL 16 or newer, installed natively or run through `infra/compose.yaml`.
- Git.

### Database

Create one role and two databases:

```sql
CREATE ROLE beautybook_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '<choose-one>';
CREATE DATABASE beautybook OWNER beautybook_app;
CREATE DATABASE beautybook_test OWNER beautybook_app;
```

Then copy `.env.example` to `.env` and set the same password in both URLs.

#### Local cluster on port 5433 (current machine setup)

This machine runs two PostgreSQL clusters:

- `postgresql-x64-16` Windows service on port `5432`. Its `postgres` superuser password is not
  known on this machine, so the project does not use it.
- A second cluster owned by the Windows user on port `5433`. The project uses this one, and `.env`
  already points at it. The password lives only in `.env`.

| Item | Value |
| --- | --- |
| Data directory | `C:\Users\pc\AppData\Local\BeautyBook\pgdata` |
| Port | `5433` (bound to `127.0.0.1` only) |
| Log | `C:\Users\pc\AppData\Local\BeautyBook\postgres.log` |

The cluster does not start automatically with Windows. Start it after a reboot:

```powershell
& 'C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe' -D 'C:\Users\pc\AppData\Local\BeautyBook\pgdata' -l 'C:\Users\pc\AppData\Local\BeautyBook\postgres.log' start
```

Stop it:

```powershell
& 'C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe' -D 'C:\Users\pc\AppData\Local\BeautyBook\pgdata' stop
```

The tables in this cluster were created with `alembic upgrade head` and are at revision `0001`.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

`/health` reports liveness and `/ready` checks PostgreSQL. Tests and checks:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

### First administrator (bootstrap)

The administrator role is never available through public registration. The first administrator is
created once, by an operator, with the administrative CLI:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.cli create-admin --email admin@beautybook.com --full-name "Site Administrator"
```

On macOS or Linux use `.venv/bin/python` instead. The command prompts for the password; when
standard input is not a terminal it reads the first line instead:

```bash
cd backend
printf '%s\n' 'a-long-password-of-at-least-12-characters' \
  | .venv/bin/python -m app.cli create-admin --email admin@beautybook.com
```

What the command does:

- Applies `alembic upgrade head` first if the tables do not exist yet.
- Creates one **active** account holding the `admin` **and** `customer` roles in a single commit.
- Hashes the password with Argon2id; the plain password is never stored, logged, or accepted as a
  command-line argument.
- Enforces the same password policy as registration (12-128 characters).
- Refuses an email that is already registered and changes nothing, so running it twice is safe.

Sign in at `http://127.0.0.1:5173/login` with that email and password. `GET /api/v1/auth/me` then
returns roles `["admin", "customer"]`, which is what the administrator screens check.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Then:

```powershell
npm run test:unit
npm run typecheck
npm run build
```

### Run both servers

Use two PowerShell terminals from the repository root:

```powershell
# Terminal 1 - backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 2 - frontend
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173/login` or `http://127.0.0.1:5173/register`. The Vite development server
proxies `/api` to `http://127.0.0.1:8000`, so both pages use the real backend and PostgreSQL.

Customer registration, login, `/auth/me`, and the administrator bootstrap command are implemented.
Logout, the account dashboard, the owner application journey, the administrator review queue, and
the administrator user list (`GET /admin/users`, F-014) are the remaining steps.

---

## 8. Guiding principles

- Build one small, correct feature at a time.
- Write the test before the implementation.
- Keep the backend authoritative for security and business rules.
- Keep the frontend focused on presentation and user experience.
- Prefer simple, proven technology over novelty.
- Never store secrets in the repository.
- Never claim something works without running it.
- Document decisions while the reason is still fresh.
- Leave the codebase easier to understand than you found it.

---

## 9. Next step

**F-001 - Authentication and registration gate.** Steps 0-5, Step 7 (login), and Step 8
(`/auth/me` and the role dependency) are implemented. Implementation continues with logout and the
remaining steps in `docs/features/F-001-authentication/PLAN.md`.
