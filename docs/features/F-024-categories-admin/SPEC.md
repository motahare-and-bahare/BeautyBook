# Feature Specification - [F-024] Service categories and the admin-only access boundary

**Status:** Done (implemented 2026-11-25; see `PLAN.md` section 10 for the completion report)
**Owning module:** `administration` (categories, admin user directory)
**Related:** F-001 (session and roles), F-002 (authorization), F-014 (full administration),
F-005 (services will reference categories later). ADR: none required - see `PLAN.md` section 1.

## 1. Problem and objective

The platform has no service taxonomy and no administrator endpoint at all: `/auth/me` returns
roles, and `require_roles` exists, but nothing is behind it. The SRS asks for a public taxonomy
(FR-CUS-004, FR-ADM-007) and the owner asked for an admin-managed `categories` table with CRUD,
proof that only `admin` can use it, and a first real admin read endpoint (the user directory).

Objective: one small, fully tested administration slice - `categories` CRUD plus a read-only
admin user directory - that proves the role boundary with real HTTP requests.

## 2. Actors and permissions

| Actor | Public taxonomy | Admin categories | Admin users |
|---|---|---|---|
| Public visitor | read active only | 401 | 401 |
| Customer | read active only | 403 | 403 |
| Salon owner | read active only | 403 | 403 |
| Administrator | read all | full CRUD | read |

The backend is authoritative. `require_roles(Role.ADMIN)` runs as a dependency, before the handler
and before any database work, and roles are re-read from the database on every request.

## 3. User journeys

1. A visitor opens the salon search page -> `GET /api/v1/categories` returns the active taxonomy
   ordered by `sort_order`, then name. Inactive categories are absent.
2. An administrator adds "کوتاهی مو" with slug `haircut` -> `201` with the created row.
3. The administrator renames it or deactivates it -> `PATCH` returns the updated row; the public
   list stops showing a deactivated category immediately.
4. The administrator deletes a category -> `204`; a second delete is `404`.
5. The administrator opens the user directory -> `GET /api/v1/admin/users?limit=20&offset=0`
   returns a page of users with their roles, never a password hash or session token.
6. A customer calls any admin endpoint -> `403 FORBIDDEN` and the handler never runs.
7. A guest calls any admin endpoint -> `401 UNAUTHENTICATED`.

### Failure paths

- Duplicate slug -> `409 CATEGORY_SLUG_TAKEN`.
- Duplicate name (case-insensitive) -> `409 CATEGORY_NAME_TAKEN`.
- Invalid slug (`Hair Cut`, `-x`, `a--b`, Persian letters) -> `422 VALIDATION_ERROR` with a field.
- Missing or stale CSRF token on a write -> `403 CSRF_INVALID`.
- Unknown category id -> `404 CATEGORY_NOT_FOUND`.

## 4. Scope

### In scope

- `categories` table via an Alembic migration, with SQLAlchemy 2.x mapping.
- Public read: `GET /api/v1/categories`.
- Admin CRUD: `GET/POST /api/v1/admin/categories`, `GET/PATCH/DELETE /api/v1/admin/categories/{id}`.
- Admin read: `GET /api/v1/admin/users` with `limit`/`offset` and a total count.
- Role and CSRF enforcement, and tests for every branch of the matrix.

### Out of scope

- Linking categories to services or salons (F-005/F-004), search filtering (F-007).
- Services, prices, availability, bookings.
- Updating, suspending, or deleting users; the directory is read-only.
- Admin UI screens; F-022's shell stays a placeholder for F-014.
- Parent/child category trees, translations, images, and icons.
- A first-administrator bootstrap command (still a recorded F-001 gap).

## 5. Functional requirements

- **FR-CAT-001 (Must):** the `categories` table exists with a unique slug, unique case-insensitive
  name, non-null name/slug, default `is_active = true`, and `sort_order` default `0`.
- **FR-CAT-002 (Must):** `GET /api/v1/categories` is public and returns only active categories.
- **FR-CAT-003 (Must):** an administrator can create, read, update, and delete a category.
- **FR-CAT-004 (Must):** duplicate name or slug is a `409`, never a `500`, including on a race.
- **FR-CAT-005 (Must):** state-changing endpoints require a valid CSRF token.
- **FR-CAT-006 (Must):** `GET /api/v1/admin/users` is admin-only, paginated, and never returns a
  password hash, session token, or other secret.
- **FR-CAT-007 (Must):** guest -> `401`, non-admin accounts -> `403`, and a denied request never
  reaches the handler.
- **FR-CAT-008 (Must):** deleting a category is a real delete today; when F-005 references
  categories the delete must become a protected operation, and that is recorded in the plan.
- **FR-CAT-009 (Should):** the public list is ordered deterministically by `sort_order`, then name.

## 6. Business rules and invariants

- Names are trimmed and stored as typed; `name_key = casefold(name)` is the uniqueness key so
  "Hair" and "hair" cannot both exist. `name_key` is internal and never returned.
- Slugs are lowercase ASCII kebab (`^[a-z0-9]+(-[a-z0-9]+)*$`, max 80) because they appear in URLs;
  a Persian display name is unaffected.
- `description` is optional, trimmed, at most 500 characters.
- Deleting or deactivating a category never rewrites unrelated data; no other table references
  categories yet.
- Every write runs in one transaction; a conflict rolls back and leaves no partial row.

## 7. UX and API behaviour

```text
GET    /api/v1/categories                  public, active only
GET    /api/v1/admin/categories            admin, includes inactive
POST   /api/v1/admin/categories            admin + CSRF, 201
GET    /api/v1/admin/categories/{id}       admin
PATCH  /api/v1/admin/categories/{id}       admin + CSRF
DELETE /api/v1/admin/categories/{id}       admin + CSRF, 204
GET    /api/v1/admin/users?limit&offset    admin
```

Errors use the single envelope from `app/core/errors.py`. Lists are ordered deterministically.
`/admin/users` returns `{items, total, limit, offset}`; `limit` is 1-100 and defaults to 20.

## 8. Data impact

New table `categories` (migration `0002`, reversible). No existing table is altered. No personal
data is added. `name_key` is derived, not user input.

## 9. Security and privacy

- Authorization and CSRF are dependencies, not handler code.
- The user directory exposes account metadata an administrator needs and nothing else; no hash,
  no token, no last-login IP.
- Category input is validated server-side; `extra="forbid"` blocks mass assignment (`id`,
  `created_at`, `name_key`).
- Slugs are ASCII-only, so no path traversal or homograph trick reaches a URL.
- Writes are logged at the same level as existing identity operations; no secrets are logged.

## 10. Edge cases

- Name longer than 80 characters or containing control characters -> `422`.
- `PATCH` with an empty body -> `422` (no accidental no-op write).
- `PATCH` that sends the same values -> `200` and unchanged `updated_at` semantics decided by the
  ORM (documented in the test).
- Deleting an already-deleted category -> `404`.
- Two admins create the same slug concurrently -> one `201`, one `409` (unique constraint, no 500).
- `limit=0` or `limit=101` -> `422`; `offset=-1` -> `422`.
- A user holding both `customer` and `admin` may use admin endpoints (any-of rule).
- A suspended account cannot use admin endpoints even with the role, because authentication
  already rejects it with `401`.

## 11. Acceptance criteria

- **AC-1:** `alembic upgrade head` creates `categories`; downgrade removes it cleanly.
- **AC-2:** the public list hides inactive categories and needs no cookie.
- **AC-3:** full admin CRUD works with a valid session and CSRF token.
- **AC-4:** guest `401`, customer `403`, salon owner `403` on every admin route.
- **AC-5:** duplicate name/slug returns `409` with the documented codes.
- **AC-6:** `/admin/users` returns roles, pagination, and no secret fields.
- **AC-7:** the full backend suite passes on SQLite, and the new integration tests also pass on
  PostgreSQL.
- **AC-8:** `ruff`, `ruff format --check`, and `mypy` are clean.

## 12. Test strategy

| Layer | What |
|---|---|
| Unit | name/slug/description rules, `name_key` derivation, invalid input matrix |
| Integration (SQLite) | migration result, CRUD over HTTP, CSRF, conflict codes, role matrix |
| Integration (PostgreSQL) | the same new tests, plus the unique-constraint race |
| Regression | existing auth/authorization/CSRF suites unchanged |

## 13. Open questions

- Should a category be soft-deleted once services reference it? Deferred to F-005, where the
  foreign key and the retention rule are defined.
- Should the user directory support search and status filters? Deferred to F-014.
