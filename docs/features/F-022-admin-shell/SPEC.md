# Feature Specification - [F-022] Admin panel shell: role-aware layout, route guard, and 403 page

**Status:** In Progress (approved by the project owner on 2026-11-24)
**Owning module:** `frontend` / `admin`
**Related:** F-001 (session and roles), F-014 (administration features - not started), ADR-0009
(authorization model). No ADR required - see `PLAN.md` section 1.

## 1. Problem and objective

`/api/v1/auth/me` already returns the caller's roles, and the backend already enforces
`require_roles`. The frontend has no shell for an administrator: no layout, no navigation, no
guard, and no access-denied page. A signed-in administrator can only see a text message.

Objective: build the **shell** an administrator will actually work in - layout, sidebar, guard,
403 page, and an honest placeholder dashboard - without inventing administration features that
F-014 has not specified yet.

## 2. Actors and permissions

- **Guest:** navigating to `/admin` is redirected to `/auth?redirect=/admin`.
- **Customer / salon owner:** sees the Persian 403 page, not the admin shell.
- **Administrator (`admin` role):** sees the admin shell.
- The backend remains the authority: every admin API call must still be rejected server-side for a
  non-admin, regardless of what the UI renders.

## 3. User journeys

1. Guest opens `/admin` -> redirected to `/auth?redirect=/admin`, and after a successful sign-in
   lands on `/admin`.
2. Customer opens `/admin` -> 403 page explains the required role and offers a way back.
3. Administrator signs in -> lands on `/admin` -> sees the shell with sections and a "under
   construction" note.
4. Administrator reloads `/admin` -> the session is restored through `/auth/me`; no flash of the
   403 page.
5. Session expires while the admin shell is open -> the next guarded navigation goes to `/auth`.

### Failure paths

- `/auth/me` unreachable (network down) -> the guard sends the user to `/auth` instead of showing
  a blank shell.
- Unknown role value -> treated as "not allowed".

## 4. Scope

### In scope

- `stores/auth.ts` (Pinia): load `/auth/me` once, expose `roles` and `hasRole`.
- `services/api/auth.ts`: add `me()`.
- `router/access.ts`: pure, testable access decision.
- Router: `/admin` (guarded), `/forbidden`.
- `modules/admin/layouts/AdminLayout.vue`, `components/AdminSidebar.vue`,
  `pages/AdminDashboardPage.vue`.
- `modules/auth/pages/ForbiddenPage.vue` with Persian copy.
- Redirect to `/admin` after sign-in when the user is an administrator.

### Out of scope

- Any F-014 feature: user list, salon moderation, settings, audit log, support actions.
- Admin user creation (no CLI command exists yet; not invented here).
- Logout (no endpoint exists yet).
- New dependencies.

## 5. Functional requirements

- **FR-ADM-001 (Must):** `/admin` is reachable only by a user whose roles include `admin`.
- **FR-ADM-002 (Must):** a guest is redirected to `/auth` with a `redirect` back to the requested
  path.
- **FR-ADM-003 (Must):** a signed-in non-admin sees the 403 page and never the admin shell.
- **FR-ADM-004 (Must):** the current user is resolved through `/auth/me` once per page load, not
  per navigation.
- **FR-ADM-005 (Must):** the sidebar only lists sections the current role may open, and marks the
  active one with `aria-current`.
- **FR-ADM-006 (Must):** the dashboard states clearly that administration features are not
  implemented yet; it must not display fake data or pretend actions work.
- **FR-ADM-007 (Must):** the access decision is a pure function covered by unit tests.
- **FR-ADM-008 (Should):** the 403 page states which role is required and links back to the
  user's own panel.

## 6. Business rules and invariants

- The UI guard is usability, not security. Every admin endpoint must still enforce roles
  server-side (`AGENTS.md` section 11).
- Roles are read from the server response, never from a client-stored role claim.
- The session cookie stays HttpOnly; no token is written to storage.
- A failed `/auth/me` is "not signed in", never "signed in with unknown roles".

## 7. UX and API behaviour

- New: `GET /api/v1/auth/me` (already exists) is called by the store.
- No new endpoint is added by this feature.
- Layout: RTL, mobile-first, sidebar collapses into a drawer under `lg`, skip-style focus order,
  visible focus ring, `aria-current` on the active link.

## 8. Data impact

None. No schema, no migration, no local storage key.

## 9. Security and privacy

- No role or identity is cached in `localStorage`; a reload re-reads `/auth/me`.
- The 403 page never reveals whether an account exists; it only compares the caller's roles.
- Admin shell renders no personal data until F-014 defines the endpoints and permissions.

## 10. Edge cases

- Deep link to a nested admin path while signed out -> `redirect` preserves the full path.
- Multiple roles (for example `customer` + `admin`) -> allowed; the check is "any of".
- Backend returns `401` -> treated as a guest.
- Backend returns `403` on `/auth/me` -> treated as a guest (defensive).
- Slow network -> the guard awaits the single in-flight request instead of firing duplicates.

## 11. Acceptance criteria

- **AC-1:** `resolveAccess` returns `allow`, `login`, and `forbidden` for the admin/customer/guest
  matrix (unit tests).
- **AC-2:** navigating to `/admin` as a guest redirects to `/auth?redirect=/admin`.
- **AC-3:** navigating to `/admin` as a customer renders the Persian 403 page.
- **AC-4:** navigating to `/admin` as an admin renders the shell, and the sidebar marks `داشبورد`
  as active.
- **AC-5:** `/auth/me` is requested once for a navigation burst, proven by the store test.
- **AC-6:** `test:unit`, `typecheck`, and `build` pass.

## 12. Test strategy

- Pure unit tests for `resolveAccess` (no DOM).
- Store test with a mocked `authApi.me` for the "one request" rule and 401 handling.
- Component tests for `AdminSidebar` (role filtering, `aria-current`) and `ForbiddenPage`
  (Persian copy, required role label).
- Router-level test with a memory history for guest redirect and customer 403.
- Regression: existing specs stay green.

## 13. Open questions

- Who creates the first administrator? Today there is no CLI command; F-014 or a small operational
  task must provide it. Recorded, not silently assumed.
- Whether the admin shell should live under a different host/subdomain is a deployment decision
  for F-018.
