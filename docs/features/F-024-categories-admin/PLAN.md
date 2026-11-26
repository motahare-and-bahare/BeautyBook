# Implementation Plan - [F-024] Service categories and the admin-only access boundary

## 1. Approach

A thin vertical slice inside the existing `administration` module, reusing `require_roles` and
`require_csrf` from `identity` instead of inventing a second auth mechanism:

```text
app/modules/administration/
  domain.py      validation for name, slug, description, name_key derivation
  models.py      Category (SQLAlchemy 2.x)
  schemas.py     CategoryCreate / CategoryUpdate / CategoryResponse / AdminUserListResponse
  repository.py  queries only
  service.py     use cases + transaction boundary + conflict mapping
  router.py      public /categories
  admin_router.py  /admin/categories and /admin/users
```

`administration` is the owner named by `docs/ARCHITECTURE.md` ("settings, categories"). The
`identity` module stays the owner of users; the admin directory calls `identity.repository` for the
user projection rather than importing the `User` model into SQL that pretends otherwise - the two
allowed patterns are a public query function or a read module, and three small query functions in
`identity.repository` (`list_users_page`, `count_users`, `roles_by_user_id`) are the smaller change.

No ADR: no dependency, no new service boundary, no consistency model change. The role gate already
exists (ADR-0009); this feature uses it.

## 2. Ordered TDD tasks

1. **Red -** `tests/unit/test_category_domain.py`: name/slug/description matrix and `name_key`.
2. **Red -** `tests/integration/test_categories_api.py`: public list, admin CRUD, conflicts, CSRF,
   role matrix.
3. **Red -** `tests/integration/test_admin_users.py`: directory shape, pagination, secrets, roles.
4. **Green -** `domain.py`, `models.py`, and migration `0002_categories`.
5. **Green -** `repository.py`, `service.py`, `schemas.py`, routers, and router wiring.
6. **Green -** `identity.repository` batch queries: `list_users_page`, `count_users`,
   `roles_by_user_id`.
7. **Refactor -** remove duplication between the two routers; keep one error-mapping helper.
8. **Verify -** focused tests, full suite on SQLite and PostgreSQL, `alembic check`, ruff, format,
   mypy.
9. **Docs -** `Task-List.md` row and change log, this report, root README endpoint list.

## 3. Schema plan

```text
categories
  id          uuid  pk
  name        varchar(80)  not null
  name_key    varchar(80)  not null  unique      -- casefold(name)
  slug        varchar(80)  not null  unique
  description text         null
  is_active   boolean      not null default true
  sort_order  integer      not null default 0
  created_at  timestamptz  not null default now()
  updated_at  timestamptz  not null default now()
  index (is_active, sort_order)
```

Why `name_key` instead of a functional `lower(name)` index: SQLite only lowercases ASCII, and
`alembic check` compares an expression index badly across both backends. A stored key is portable,
deterministic, and testable.

## 4. API and error mapping

| Situation | Status | Code |
|---|---|---|
| unknown id | 404 | `CATEGORY_NOT_FOUND` |
| slug reused | 409 | `CATEGORY_SLUG_TAKEN` |
| name reused (any case) | 409 | `CATEGORY_NAME_TAKEN` |
| invalid field | 422 | `VALIDATION_ERROR` + `fields` |
| guest on admin route | 401 | `UNAUTHENTICATED` |
| non-admin on admin route | 403 | `FORBIDDEN` |
| stale CSRF on write | 403 | `CSRF_INVALID` |

## 5. Test plan

| Layer | What |
|---|---|
| Unit | pure validation: trimming, length, control characters, slug grammar, `name_key` |
| Integration | 20+ HTTP cases: public visibility, CRUD, conflicts, CSRF, role matrix, pagination |
| PostgreSQL | the same file with `TEST_DATABASE_URL`, plus a unique-constraint race |
| Regression | the 269 existing backend tests and 80 frontend tests |

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Role check forgotten on a new route | A parametrised test hits every admin route as guest/customer/owner |
| Case-variant duplicate names | `name_key` unique constraint, tested with `Hair`/`hair` |
| Delete becomes unsafe when services exist | Recorded: F-005 adds the FK and switches to protected/soft delete |
| `PATCH` used for mass assignment | `extra="forbid"` and no writable `id`/`created_at`/`name_key` |
| Pagination on an unbounded table | `limit` is capped at 100 and the total comes from a count query |
| Secrets leak into the directory | Explicit response schema; test asserts the serialized body has no hash/token |

## 7. Rollout and rollback

Additive table and routers. Rollback: `alembic downgrade 0001` drops `categories`; removing the
router includes restores the previous API. No existing behaviour changes.

## 8. Documentation

- `Task-List.md`: F-024 row, status, change-log entry.
- `docs/ARCHITECTURE.md` module table already lists categories under `administration`; no change.
- `backend/README` or root `README` endpoint list: add the new routes.
- F-014 stays the owner of moderation, settings, audit, and user write actions.

## 9. Completion checklist

- [x] Unit tests written first and observed failing
- [x] Migration created, upgrade and downgrade verified
- [x] Public list hides inactive categories
- [x] CRUD enforces admin + CSRF
- [x] Guest 401 / customer 403 / owner 403 proven on every admin route
- [x] Conflicts return 409, never 500
- [x] Directory returns no secrets and is paginated
- [x] SQLite and PostgreSQL suites pass
- [x] `alembic check`, ruff, format, mypy clean
- [x] Task-List and README updated

## 10. Completion report (2026-11-25)

### What was requested

Add a `categories` table with a SQLAlchemy model and CRUD APIs, prove that `admin` can use the
administrator APIs (list users, manage categories) while `customer` and `salon_owner` cannot, and
write and run tests. Services and pricing were explicitly out of scope.

### What was built

| Area | Change |
|---|---|
| Domain | `app/modules/administration/domain.py`: name/slug/description rules, `name_key` |
| Model | `app/modules/administration/models.py`: `Category` |
| Migration | `migrations/versions/0002_categories.py` (`down_revision = "0001"`) |
| Queries | `administration/repository.py`; `identity/repository.py` gained three batch queries |
| Use cases | `administration/service.py`: CRUD, conflict mapping, paginated directory |
| Schemas | `administration/schemas.py`: create/update/response, admin user list |
| HTTP | `administration/router.py` (public), `administration/admin_router.py` (admin) |
| Wiring | `app/api/v1/router.py`, `migrations/env.py` |
| Tests | `tests/unit/test_category_domain.py`, `tests/integration/test_categories_api.py`, `tests/integration/test_admin_users.py`, fixtures in `tests/conftest.py` |

### Behaviour

- Public `GET /api/v1/categories` returns active categories only, ordered by `sort_order` then name,
  and needs no cookie.
- Administrator CRUD: `GET/POST /api/v1/admin/categories`, `GET/PATCH/DELETE
  /api/v1/admin/categories/{id}`. Writes are `201`/`200`/`204`; an unknown id is `404`.
- `GET /api/v1/admin/users?limit=&offset=` returns `{items, total, limit, offset}` with roles and no
  secrets.
- Order of checks on admin routes: authenticate (`401`), authorize (`403`), then CSRF (`403
  CSRF_INVALID`) only for an authenticated administrator.

### Commands actually run and exact results

Run from `backend/` with `.venv\Scripts\python.exe`:

| Command | Result |
|---|---|
| `pytest tests/unit/test_category_domain.py tests/integration/test_categories_api.py tests/integration/test_admin_users.py -q` | **72 passed** (Red was observed first: `ModuleNotFoundError` for `administration.domain`, then the missing `categories` table) |
| `pytest -q` (SQLite) | **341 passed, 1 skipped** (the skip is the PostgreSQL-only registration race) |
| `pytest -q` with `TEST_DATABASE_URL` pointing at `beautybook_test` on PostgreSQL 5433 | **341 passed, 1 skipped** (now the registration race runs; the skip is the SQLite-profile test) |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 64 files already formatted |
| `mypy app` | Success: no issues found in 31 source files |
| `alembic upgrade head` -> `alembic check` -> `downgrade 0001` -> `upgrade head` on a temporary SQLite file | Upgrade succeeded, `No new upgrade operations detected`, downgrade and re-upgrade succeeded, then the temporary database was deleted |
| `alembic upgrade head` + `alembic check` on the development SQLite database | 0001 -> 0002 applied, `No new upgrade operations detected`, `categories` present with 0 rows |

### Not run, and why

- No concurrency test for two simultaneous `POST /admin/categories` with the same slug. The unique
  constraint and its `IntegrityError` mapping are in place and unit-covered through the pre-check,
  but a two-request race test is not written. Follow-up, not a claim.
- No live browser or `curl` check against a running server: no command exists that creates the first
  administrator account, so an administrator session cannot be obtained outside the test fixtures.
  The role boundary is therefore proven by integration tests that insert an administrator row and a
  real database session, not by a manual login.
- Frontend: unchanged. The admin shell (F-022) still shows placeholders; wiring these endpoints into
  screens belongs to F-014.

### Known limitations and follow-ups

1. **No first-administrator bootstrap.** Recorded F-001 gap; without it the admin API is reachable
   only from tests or a manual database insert.
2. **Delete is a hard delete.** Acceptable while nothing references `categories`; F-005 must add the
   foreign key and switch to protected/soft deletion before services exist.
3. **The public taxonomy has no pagination.** Intended for a small, curated list; revisit if the list
   can grow unbounded.
4. **Conflicts are detected twice** (pre-check plus unique constraint). The second path exists for
   the race and maps to the same codes; the extra read is cheap and keeps error codes stable.
