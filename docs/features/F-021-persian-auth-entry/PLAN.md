# Implementation Plan - [F-021] Persian combined sign-in / sign-up entry

## 1. Approach

A pure component extraction, not a rewrite:

```text
pages/LoginPage.vue            -> AuthLayout + <LoginForm />
pages/RegisterCustomerPage.vue -> AuthLayout + <RegisterCustomerForm />
pages/AuthPage.vue             -> AuthLayout + tab strip + one of the two forms
```

Why extraction instead of copy: the forms carry ~600 lines of validation, API calls, Persian
error mapping, focus management, and success panels. A second copy would drift the moment one
side changes, and `AGENTS.md` forbids duplicating backend rules in the frontend.

No ADR is required: no new dependency, no new module boundary, no data or API change. The page
follows ADR-0007 (plain CSS with tokens) and ADR-0009 (the backend stays authoritative).

## 2. Ordered TDD tasks

1. **Red -** `tests/unit/auth-entry.spec.ts`:
   - `/auth` renders the sign-in form;
   - `?mode=register` renders the sign-up form and any other value falls back;
   - the active tab exposes `aria-current="page"`;
   - `?redirect=` is honoured after sign-in and rejected when external;
   - the sign-in form inside `/auth` calls the same API with the same normalisation.
2. **Red -** `tests/unit/redirect.spec.ts` for the pure `safeRedirect()` helper
   (accepts `/admin`, `/account?tab=1`; rejects `//evil.com`, `https://evil.com`, `admin`,
   `javascript:`).
3. **Green -** extract `components/LoginForm.vue` and `components/RegisterCustomerForm.vue`
   without changing markup, ids, or messages.
4. **Green -** `pages/AuthPage.vue` with two `RouterLink` tabs and `?mode=` parsing.
5. **Green -** `utils/redirect.ts` and the post-login navigation.
6. **Refactor -** thin wrappers for `/login` and `/register`; delete duplicated markup.
7. **Verify -** `npm run test:unit`, `npm run typecheck`, `npm run build`, then a live check.

## 3. API and data plan

No change. `authApi.login`, `authApi.registerCustomer`, and the CSRF contract are reused.

## 4. Test plan

| Layer | What |
|---|---|
| Unit | `AuthPage` tab selection, deep links, redirect handling, API call |
| Unit | `safeRedirect` matrix |
| Regression | The five existing frontend specs, unchanged |
| Manual | Live server: open `/auth`, switch tabs, submit both forms |

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Extraction breaks the existing DOM tests | Keep ids, labels, and wording identical; run the old specs first |
| Tab strip is keyboard-inaccessible | Use real links plus `aria-current`, not click handlers |
| Open redirect through `?redirect=` | `safeRedirect()` accepts only local absolute paths |
| Two sources of truth drift again | The old pages render the same components; a test asserts it |

## 6. Rollout and rollback

Additive: a new route. Rollback = delete `/auth` and the two form components, restore the pages.
No data involved.

## 7. Documentation

- `Task-List.md` row F-021 and change-log entry.
- `README.md`: mention the `/auth` entry point in the getting-started section.
- `SPEC.md` stays the source of truth for behaviour.

## 8. Completion checklist

- [x] Tests written first and observed failing
- [x] `/auth` and `?mode=` behave as specified
- [x] `/login` and `/register` still pass their tests
- [x] No duplicated validation or API code
- [x] Redirect safety tested
- [x] `test:unit`, `typecheck`, `build` clean
- [x] Live check done
- [x] Task-List and README updated

## 9. Completion report (2026-11-24)

**Delivered**

| File | Role |
|---|---|
| `src/modules/auth/components/LoginForm.vue` | the previous login page body, unchanged markup and messages |
| `src/modules/auth/components/RegisterCustomerForm.vue` | the previous registration page body |
| `src/modules/auth/pages/LoginPage.vue`, `RegisterCustomerPage.vue` | thin `AuthLayout` wrappers around the two components |
| `src/modules/auth/pages/AuthPage.vue` | tab strip, `?mode=` parsing, redirect handling |
| `src/utils/redirect.ts` | `safeRedirect()` |
| `src/router/index.ts` | `/auth` route and `/` -> `/auth` |

**Red -> Green evidence**

1. Red: five new specs (`access`, `redirect`, `auth-entry`, `auth-store`, `admin-shell`,
   `admin-router`) plus the updated `app.spec.ts` failed for the intended reasons
   (`createAppRouter is not a function`, missing tabs, `/` still going to `login`).
2. Green: after the components, helper, and route existed, `vitest run` reported
   **11 files / 74 tests passed**.
3. Refactor: the two old pages now contain no validation, API, or error-mapping code.

**Commands actually run**

| Command | Result |
|---|---|
| `& 'C:\Program Files\nodejs\npm.cmd' run test:unit` | 11 files, 74 tests passed |
| `& 'C:\Program Files\nodejs\npm.cmd' run typecheck` | no output, exit 0 |
| `& 'C:\Program Files\nodejs\npm.cmd' run build` | 65 modules, `dist/` emitted, 426 ms |
| live `npm run dev` on `http://localhost:5173` | `/auth` rendered with `lang="fa" dir="rtl"`; `/auth?mode=register` rendered four inputs; tab `aria-current` correct |

**Not run / known limits**

- No real sign-in was performed: that needs an existing account, and creating one would write to
  the development database without the owner's approval.
- `?redirect=` was proven by unit tests and by the admin guard redirect, not by a manual browser
  round trip.
- `/login` and `/register` are kept and not yet redirects to `/auth`; that is a later product
  decision.

**Operational note added during the live check**

The Vite dev server now sets `host: '127.0.0.1'` and `strictPort: true`. Node resolves `localhost`
to `::1` first, so the server was listening on IPv6 only, and the documented
`http://127.0.0.1:5173` URL returned a proxy error. A second instance also silently moved to `5174`
while the README still said `5173`. Loopback IPv4 matches the README and the `/api` proxy target
and keeps the server off the LAN; `strictPort` makes a port clash visible.
