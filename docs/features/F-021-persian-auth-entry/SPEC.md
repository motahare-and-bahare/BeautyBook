# Feature Specification - [F-021] Persian combined sign-in / sign-up entry

**Status:** In Progress (approved by the project owner on 2026-11-24)
**Owning module:** `frontend` / `auth`
**Related:** F-001 (authentication API), F-019 (Persian RTL auth screens). No ADR required - see
`PLAN.md` section 1.

## 1. Problem and objective

Two working Persian screens already exist (`/login`, `/register`), but they are separate
destinations. A visitor who lands on the product has to guess which one to open, and the
"don't have an account?" round trip is slow on mobile.

Objective: one entry point, `/auth`, that offers both forms as two tabs, keeps the current
deep links working, and reuses the existing forms instead of duplicating a single line of
validation, API, or error-mapping logic.

## 2. Actors and permissions

- **Public visitor:** may open `/auth` and switch between the two forms.
- **Signed-in user:** still sees the success panel of the form they submitted.
- No authorization change. The entry point is public by design.

## 3. User journeys

1. Visitor opens `/auth` -> the sign-in tab is active, focus lands on the page heading.
2. Visitor opens `/auth?mode=register` -> the sign-up tab is active (deep link, shareable).
3. Visitor switches tabs -> the URL changes, the other form renders, no page reload.
4. Visitor submits the sign-in form -> identical behaviour to `/login` (same API, same Persian
   messages, same rate-limit/CSRF handling).
5. Visitor submits the sign-up form -> identical behaviour to `/register`.
6. Visitor arrives from a protected page with `?redirect=/admin` -> after a successful sign-in the
   app navigates to the redirect target.

### Failure paths

- Unknown `mode` value (for example `?mode=xyz`) -> sign-in tab is shown, no error.
- Validation and API errors -> unchanged Persian messages, focus moves to the first invalid field.

## 4. Scope

### In scope

- Extract the inner form of `LoginPage.vue` into `components/LoginForm.vue`.
- Extract the inner form of `RegisterCustomerPage.vue` into `components/RegisterCustomerForm.vue`.
- New page `pages/AuthPage.vue` with two tab links and the active form.
- Keep `/login` and `/register` working as thin wrappers (no duplicated logic).
- Sync the active tab with `?mode=` in the URL.
- Safe redirect handling for `?redirect=`.

### Out of scope

- Owner sign-up, password reset, email verification, logout.
- Any new dependency.
- Redesigning the visual language: the existing `AuthLayout` and design tokens are reused as-is.

## 5. Functional requirements

- **FR-AUTH-001 (Must):** `/auth` renders the sign-in form by default.
- **FR-AUTH-002 (Must):** `/auth?mode=register` renders the sign-up form; any other value falls
  back to sign-in.
- **FR-AUTH-003 (Must):** switching tabs changes the URL without a full page reload.
- **FR-AUTH-004 (Must):** `/login` and `/register` keep their behaviour and deep links.
- **FR-AUTH-005 (Must):** no validation, API call, or Persian message is duplicated between the
  old pages and the new entry point; both render the same components.
- **FR-AUTH-006 (Must):** the tab links are real links (keyboard reachable, middle-click and
  back button work) and expose the active tab through `aria-current`.
- **FR-AUTH-007 (Must):** after a successful sign-in with a valid `?redirect=`, navigation goes to
  that in-app path; external or malformed targets are ignored.
- **FR-AUTH-008 (Should):** the browser title reflects the active tab.
- **FR-AUTH-009 (Must):** `/` redirects to `/auth`, so a first-time visitor lands on the combined
  entry point instead of an arbitrary half of it.

## 6. Business rules and invariants

- The backend stays authoritative for validation, credentials, and session creation.
- The frontend only validates for usability; the server response wins.
- `redirect` must be a local absolute path (`/...`), never an external URL. This is the same rule
  the backend already applies to safe redirects.
- Persian labels come from `modules/auth/labels.ts`; no raw English enum reaches the UI.

## 7. UX and API behaviour

- No API change. `authApi.login` and `authApi.registerCustomer` are the only calls.
- Layout: one `AuthLayout` card with a two-link tab strip above the form; mobile-first, RTL.
- Loading, error, and success states are inherited from the existing forms.

## 8. Data impact

None. No new storage, no new cookies, no schema change.

## 9. Security and privacy

- No credential is persisted in `localStorage` or `sessionStorage`; the existing HttpOnly session
  cookie and in-memory CSRF token are unchanged.
- The redirect target is validated in the frontend and remains validated by the backend.
- Password fields keep `dir="ltr"` and `autocomplete` hints.

## 10. Edge cases

- `?mode=` empty, repeated, or array-like -> first value is used, invalid values ignored.
- Very long email -> the existing 254-character guard applies.
- Sign-in succeeds while the user is already signed in -> unchanged behaviour (new session).
- Back button between tabs -> the correct form is restored from the URL.

## 11. Acceptance criteria

- **AC-1:** `/auth` shows the sign-in form; `/auth?mode=register` shows the sign-up form.
- **AC-2:** clicking the other tab updates the URL and swaps the form without reloading.
- **AC-3:** `/login` and `/register` still pass their existing tests.
- **AC-4:** both forms are rendered from the same components in the old pages and the new page.
- **AC-5:** a successful sign-in with `?redirect=/admin` navigates to `/admin`; `?redirect=//evil.com`
  does not navigate away from the app.
- **AC-6:** `npm run test:unit`, `npm run typecheck`, and `npm run build` pass.
- **AC-7:** `/` redirects to `/auth` without a redirect chain.

## 12. Test strategy

- Unit (Vitest + Vue Test Utils + jsdom): default tab, `?mode=` handling, tab navigation, sign-in
  API call from the new entry point, redirect safety helper.
- Regression: the existing `login-form.spec.ts`, `register-customer-form.spec.ts`, `rtl-persian.spec.ts`,
  `app.spec.ts`, `api-client.spec.ts` must stay green.
- Manual: open `/auth`, switch tabs, sign in with a real local account.

## 13. Open questions

None blocking. Whether `/login` and `/register` should eventually redirect to `/auth` is a product
decision for later; today they stay as thin wrappers so existing links do not break.
