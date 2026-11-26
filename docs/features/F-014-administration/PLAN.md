# PLAN - F-014 Administration, increment 1: administrator user list

**Task:** F-014 (increment 1) | **SPEC:** `docs/features/F-014-administration/SPEC.md`
**Status:** Implemented (2026-11-25)

## 1. Ordered implementation steps (TDD)

| Step | Work |
|---|---|
| 1 | Red: unit tests for cursor encode/decode and limit bounds in `tests/unit/test_admin_pagination.py`. |
| 2 | Green: `administration/domain.py` — opaque base64 cursor, UTC normalization, `INVALID_CURSOR`, `INVALID_PAGE_LIMIT`. |
| 3 | Red: integration tests in `tests/integration/test_admin_users_list.py` for ordering, roles, pagination, `401`/`403`, invalid cursor, limit bounds, secrets absent. |
| 4 | Green: `administration/repository.py` keyset page query plus one batched role query (no N+1). |
| 5 | Green: `administration/service.py` fetches `limit + 1` rows, issues `next_cursor` only when more data exists. |
| 6 | Green: `administration/schemas.py`, `administration/router.py` (`GET /admin/users`, admin role dependency), mounted in `app/api/v1/router.py`. |
| 7 | Red: frontend tests in `tests/unit/admin-users.spec.ts` and `tests/unit/router-guard.spec.ts`. |
| 8 | Green: `services/api/admin.ts`, `stores/auth.ts`, `modules/admin/pages/AdminUsersPage.vue`, `modules/auth/pages/ForbiddenPage.vue`, router guard and routes. |
| 9 | Refactor and documentation: Task-List, this PLAN, SPEC, README where the remaining F-001 steps are listed. |

## 2. Files

- `backend/app/modules/administration/{__init__,domain,repository,schemas,service,router}.py`
- `backend/app/api/v1/router.py`
- `backend/tests/unit/test_admin_pagination.py`
- `backend/tests/integration/test_admin_users_list.py`
- `frontend/src/services/api/admin.ts`, `frontend/src/services/api/auth.ts` (`me()`)
- `frontend/src/stores/auth.ts`
- `frontend/src/modules/admin/pages/AdminUsersPage.vue`
- `frontend/src/modules/auth/pages/ForbiddenPage.vue`, `LoginPage.vue` (admin link)
- `frontend/src/router/index.ts`
- `frontend/tests/unit/admin-users.spec.ts`, `frontend/tests/unit/router-guard.spec.ts`

## 3. Decisions and trade-offs

- **Keyset cursor instead of offset/`page` parameters.** Offset pagination duplicates or skips
  rows when accounts are created between requests; the cursor costs a slightly larger query but
  keeps every row exactly once. The trade-off is that only "next" is supported. The UI needs
  exactly that.
- **Reuse of `identity.schemas.UserResponse`.** It is already the canonical safe account shape. A
  duplicate schema would drift from `/auth/me` and risk exposing a new field by accident.
- **Role check in the router dependency.** Same mechanism as F-001 Step 8, so `401` and `403`
  stay consistent and the handler cannot run unauthorized.
- **`/forbidden` page instead of redirecting a signed-in customer to login.** Sending a
  signed-in user to login hides the real reason; the 403 page states it.
- **Cursor is opaque, not signed.** It contains no secret and only reorders a query the caller is
  already allowed to run, so signing adds no security. A malformed value is rejected.

## 4. Migration and rollback

None. No schema change: rollback is reverting the code.

## 5. Verification

| Check | Command |
|---|---|
| Backend lint/format/types | `ruff check .`, `ruff format --check .`, `mypy` |
| Backend tests (PostgreSQL) | `pytest` |
| Frontend tests | `npm run test:unit` |
| Frontend types and build | `npm run typecheck`, `npm run build` |

## 6. Risks and mitigations

| Risk | Mitigation |
|---|---|
| PII exposure through a list endpoint | Fixed field set, no hashes or tokens, integration test asserts the exact keys |
| N+1 role queries | One batched role query per page |
| Unstable ordering with equal `created_at` | `id` is the tie-breaker, so the order is total |
| Guarded UI mistaken for security | Backend test proves `403` without the role; the UI never decides access |

## 7. Completion checklist

- [x] SPEC and PLAN written before the implementation.
- [x] Tests written first; each acceptance criterion has a test.
- [x] Backend lint, format, and type checks pass.
- [x] Backend suite passes against PostgreSQL.
- [x] Frontend unit tests, typecheck, and build pass.
- [x] Task-List updated.
- [ ] Audit-log record for reading the user list (deferred to the audit-storage task in F-014).
- [ ] Search and filters (deferred to the next F-014 increment).
