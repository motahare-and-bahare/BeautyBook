# Implementation Plan - [F-019] Persian localization and RTL layout for the authentication screens

## 1. Implementation approach

Presentation-only change driven by tests. The existing Vitest suite already asserts English copy,
so it is the natural first red signal. Update the suite to the Persian expectations, add a static
assertion test for `index.html` and `tokens.css`, then implement the copy and direction changes
until the suite is green.

No backend file changes. No new dependency. No migration.

## 2. Preconditions

- F-001 authentication screens exist and pass their tests.
- Node and npm are available; `npm.cmd run test:unit` works.

## 3. Ordered TDD tasks

### Test-first order

1. **Red** - update `tests/unit/app.spec.ts` to expect the Persian heading.
2. **Red** - update `tests/unit/login-form.spec.ts` to the Persian validation and error messages,
   and assert `#email` has `dir="ltr"`.
3. **Red** - update `tests/unit/register-customer-form.spec.ts` to the Persian messages and the
   Persian role label.
4. **Red** - add `tests/unit/rtl-persian.spec.ts` reading `index.html` (`lang="fa"`, `dir="rtl"`)
   and `tokens.css` (`Vazirmatn` in `--font-sans`).
5. Run the suite and confirm the new expectations fail for the intended reason.
6. **Green** - translate `AuthLayout.vue`, `LoginPage.vue`, `RegisterCustomerPage.vue`, and add the
   `dir` prop to `FormField.vue`.
7. **Green** - set `lang="fa"` and `dir="rtl"` in `index.html`.
8. **Green** - update the font stack in `tokens.css`.
9. **Green** - directional CSS fixes: `text-align: start`, logical inset properties, remove
   `letter-spacing`/`text-transform` from Persian labels.
10. **Refactor** - extract shared Persian label maps for roles and statuses if duplication appears.
11. **Verify** - `npm run test:unit`, `npm run typecheck`, `npm run build`, then a manual browser
    check.

## 4. Database and migration plan

None. No schema or data change, so no migration and no rollback script.

## 5. API and frontend plan

### API

Unchanged.

### Frontend

| File | Change |
| --- | --- |
| `index.html` | `lang="fa"`, `dir="rtl"`, Persian title |
| `src/assets/styles/tokens.css` | Persian-first `--font-sans` |
| `src/modules/auth/components/AuthLayout.vue` | Persian brand panel copy, `text-align: start`, logical insets |
| `src/modules/auth/components/FormField.vue` | optional `dir` prop forwarded to the input |
| `src/modules/auth/pages/LoginPage.vue` | Persian copy, Persian error map, `dir="ltr"` on email/password |
| `src/modules/auth/pages/RegisterCustomerPage.vue` | Persian copy, Persian error map, Persian field-error mapping |

## 6. Test plan

- Unit: Persian copy, validation messages, error-code mapping, duplicate-email path, `dir`
  attributes, role/status labels.
- Static: `index.html` and `tokens.css` assertions.
- Manual: browser check of both pages at desktop and mobile widths, keyboard focus order, and the
  success panels.

## 7. Observability and operations

No change.

## 8. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| English backend field messages leak into the UI | Map known fields to Persian text when the code is `VALIDATION_ERROR` |
| Persian text breaks because of `letter-spacing` | Remove letter spacing on Persian labels |
| Latin emails render reversed inside RTL text | `dir="ltr"` on email/password inputs, `<strong>` around the address |
| Accessibility regression | Keep every `label for`, `aria-*` attribute and `role="alert"` |

## 9. Rollout and rollback

Rollout: normal frontend deployment. Rollback: revert the commit; no data is affected.

## 10. Documentation updates

- `Task-List.md`: add F-019 and a change-log entry.
- `README.md`: note that the authentication screens are Persian and RTL.
- `frontend/README.md`: note the Persian/RTL state of the auth screens.

## 11. Completion checklist

- [x] Tests written first and observed failing
- [x] Persian copy applied to every in-scope screen
- [x] `dir="rtl"` and `lang="fa"` present
- [x] Persian font stack configured
- [x] `npm run test:unit` passes
- [x] `npm run typecheck` passes
- [x] `npm run build` passes
- [x] Manual browser check performed
- [x] Task-List and README updated

## 12. Completion report

**What changed**

- `index.html`: `lang="fa"`, `dir="rtl"`, Persian document title.
- `src/assets/styles/tokens.css`: Persian-first `--font-sans` (`Vazirmatn`, `Vazir`, `IRANSans`,
  `Noto Sans Arabic`, `Tahoma`, `Segoe UI`, system fallbacks).
- `src/modules/auth/labels.ts` (new): Persian labels for roles, statuses and backend field errors.
- `AuthLayout.vue`, `LoginPage.vue`, `RegisterCustomerPage.vue`: Persian copy, RTL-safe CSS
  (`text-align: start`, `inset-inline-end`, no letter spacing on Persian text, larger line height).
- `FormField.vue`: new `dir` prop so Latin input content stays left to right.

**Commands executed and results**

- `npm.cmd run test:unit` -> 25 passed across 5 files (Red first: 19 failed with the intended
  English-copy and missing-`dir` reasons).
- `npm.cmd run typecheck` -> exit 0.
- `npm.cmd run build` -> built successfully, 40 modules.

**Manual browser verification**

Live page at `http://127.0.0.1:5173` against the running backend:

- `document.documentElement.lang` -> `fa`, `dir` -> `rtl`.
- Login heading -> «ورود به بیوتی‌بوک»; labels -> «ایمیل», «رمز عبور»; `#email` `dir="ltr"`.
- Empty login submit -> «ایمیل خود را وارد کنید.» and «رمز عبور را وارد کنید.».
- Wrong password -> «ایمیل یا رمز عبور نادرست است.».
- Registration -> Persian success panel with نقش «مشتری» and وضعیت «فعال».
- Duplicate email -> «حسابی با این ایمیل از قبل وجود دارد…» with the sign-in link.

**What was not run and why**

- No screenshot was captured: the desktop app window was not visible to the browser tool, so
  `browser.screenshot` was unavailable. Verification used the DOM and accessibility tree instead.
- No end-to-end (Playwright) suite exists yet; it is scheduled in F-001.
- No backend tests were re-run because no backend file changed.

**Known limitations**

- Vazirmatn renders only for users who have it installed; otherwise the stack falls back to
  Tahoma/Segoe UI. Bundling the font would need an ADR.
- Only the authentication screens are localized. Other future screens still need the same
  treatment.
- Copy lives inside components; adding a second locale later requires extracting it.

**Follow-up tasks**

- Decide in a future feature whether to bundle Vazirmatn and adopt an i18n framework.
- Apply the same RTL/Persian conventions to the remaining screens as they are built.
