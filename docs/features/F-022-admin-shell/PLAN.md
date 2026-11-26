# Implementation Plan - [F-022] Admin panel shell

## 1. Approach

Build the smallest honest shell. "Admin panel" here means the frame an administrator will use -
not the administration features, which are `F-014` and must be specified before code. Delivering
fake tables or mock users would violate `AGENTS.md` (no unregistered feature work, no pretending).

No ADR is required: no dependency, no persistence, no module boundary change. The guard implements
ADR-0009 client-side usability while the backend keeps the authority.

## 2. Ordered TDD tasks

1. **Red -** `tests/unit/access.spec.ts`: the pure decision matrix.
2. **Red -** `tests/unit/admin-shell.spec.ts`: sidebar filtering and `aria-current`, 403 page copy,
   dashboard placeholder text.
3. **Red -** `tests/unit/auth-store.spec.ts`: one `/auth/me` call for concurrent callers, `401` ->
   guest, `roles` exposed.
4. **Red -** `tests/unit/admin-router.spec.ts`: guest redirect with `?redirect=`, customer 403,
   admin allowed (memory history).
5. **Green -** `services/api/auth.ts`: `me()`.
6. **Green -** `stores/auth.ts`.
7. **Green -** `router/access.ts`.
8. **Green -** `ForbiddenPage.vue`, `AdminLayout.vue`, `AdminSidebar.vue`,
   `AdminDashboardPage.vue`.
9. **Green -** wire routes and `beforeEach` in `router/index.ts`.
10. **Green -** after sign-in, send an administrator to `/admin` (or to `?redirect=`).
11. **Refactor -** share the panel-path helper between the login form, the 403 page, and the guard.
12. **Verify -** unit tests, typecheck, build, live check.

## 3. File and module plan

```text
src/
  services/api/auth.ts          me()
  stores/auth.ts                useAuthStore
  router/access.ts              resolveAccess()  (pure)
  router/index.ts               routes + beforeEach
  modules/admin/
    layouts/AdminLayout.vue     shell: sidebar + header + <slot>
    components/AdminSidebar.vue items, active state, mobile drawer
    pages/AdminDashboardPage.vue placeholder + honest note
  modules/auth/pages/ForbiddenPage.vue
```

## 4. Test plan

| Layer | What |
|---|---|
| Pure unit | `resolveAccess` guard matrix, `safeRedirect` |
| Store unit | single in-flight `/auth/me`, `401` handling |
| Component | sidebar role filtering, `aria-current`, 403 copy |
| Router | guest redirect, customer 403, admin allowed |
| Regression | all existing specs |

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Guard becomes the only protection | The SPEC states the backend stays authoritative; no admin endpoints exist yet |
| Flash of 403 on reload | The guard awaits `/auth/me` before deciding |
| Duplicate `/auth/me` calls | One shared promise in the store, tested |
| Fake admin data sneaks in | Dashboard renders no data at all, only a note and section placeholders |
| Sidebar marks wrong item active | `aria-current` asserted in a component test |

## 6. Rollout and rollback

Additive routes. Rollback = remove `/admin`, `/forbidden`, and the store; no data to migrate.

## 7. Documentation

- `Task-List.md`: F-022 row and change-log entry.
- `README.md`: how to reach `/admin` and the honest statement that F-014 is not implemented.
- `SPEC.md` remains the behaviour contract.

## 8. Completion checklist

- [x] Access matrix tested first
- [x] Guard redirects guests and blocks non-admins
- [x] One `/auth/me` per page load
- [x] Sidebar role-aware and accessible
- [x] 403 page in Persian with the required role
- [x] No fabricated admin data
- [x] `test:unit`, `typecheck`, `build` clean
- [x] Live check done
- [x] Task-List and README updated

## 9. Completion report (2026-11-24)

**Delivered**

| File | Role |
|---|---|
| `src/stores/auth.ts` | Pinia store, one shared in-flight `GET /auth/me`, `roles`, `hasRole`, `reload` |
| `src/router/access.ts` | pure `resolveAccess()` decision |
| `src/router/index.ts` | `createAppRouter(history)` factory, `/admin` with a guarded `:section` child, `/forbidden` |
| `src/modules/admin/layouts/AdminLayout.vue` | sidebar + header + slot |
| `src/modules/admin/components/AdminSidebar.vue` | role-filtered menu, `aria-current`, `aria-disabled` "به‌زودی" items |
| `src/modules/admin/pages/AdminDashboardPage.vue` | honest "not implemented" placeholder |
| `src/modules/admin/pages/AdminSectionPage.vue` | guarded placeholder for deep links such as `/admin/users` |
| `src/modules/auth/pages/ForbiddenPage.vue` | Persian 403 with the required role label |

**Design notes**

- `/admin/:section` exists so a deep link is *guarded* rather than 404. It renders a placeholder
  and never queries the backend, because F-014 has not defined those endpoints.
- The dashboard deliberately renders no counts, tables, or buttons that would imply working
  administration.
- `createAppRouter(history)` was extracted so router-level tests run on a memory history.

**Commands actually run**

| Command | Result |
|---|---|
| `& 'C:\Program Files\nodejs\npm.cmd' run test:unit` | 11 files, 74 tests passed (includes `access`, `auth-store`, `admin-shell`, `admin-router`) |
| `& 'C:\Program Files\nodejs\npm.cmd' run typecheck` | exit 0 |
| `& 'C:\Program Files\nodejs\npm.cmd' run build` | production build succeeded |
| live `GET /admin` as a guest | redirected to `/auth?redirect=/admin`; `GET /api/v1/auth/me` returned `401` through the Vite proxy |

**Not run / known limits**

- **No administrator could be created**, so the authenticated admin shell was not viewed in a real
  browser. There is no bootstrap CLI command; this is a recorded gap, not something invented here.
- The 403 page was verified by component and router tests, not by a browser session with a real
  customer account.
- The guard is usability only. No admin endpoint exists yet; when F-014 adds one it must use
  `require_roles("admin")` server-side.
