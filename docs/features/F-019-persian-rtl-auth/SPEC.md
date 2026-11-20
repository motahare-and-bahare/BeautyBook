# Feature Specification - [F-019] Persian localization and RTL layout for the authentication screens

**Status:** Ready (approved directly by the project owner)

## 1. Problem and objective

The customer-facing authentication screens (`/login` and `/register`) are written in English and
laid out left to right. The product is aimed at Iranian users, so the screens must be readable in
Persian and laid out right to left.

Objective: make every visible string on the login and customer-registration screens Persian, make
the whole document right to left, and use a Persian-capable font stack, without changing any
backend behaviour or any API contract.

## 2. Actors and permissions

- **Public visitor / customer**: reads the screens and submits the forms. No permission change.
- **Salon owner / administrator**: not affected by this feature beyond seeing the same screens.

This feature touches presentation only. It must not change authorization, sessions, CSRF handling,
or validation authority.

## 3. User journeys

### Primary journey

1. A visitor opens `/register`.
2. The page appears in Persian, right to left, with Persian labels, placeholders, hint text and
   button captions.
3. The visitor submits valid data and sees a Persian success panel.
4. The visitor opens `/login`, signs in, and sees a Persian success panel.

### Alternative paths

- The visitor submits invalid data and sees Persian field errors.
- The visitor submits a duplicate email and sees a Persian explanation plus a link to sign in.
- The visitor enters a wrong password and sees the generic Persian invalid-credentials message.

### Failure paths

- The backend is unreachable: a Persian "cannot reach the server" message appears.
- The CSRF token expired: a Persian "security token expired" message appears.

## 4. Scope

### In scope

- `LoginPage.vue`, `RegisterCustomerPage.vue`, `AuthLayout.vue`, `FormField.vue`.
- `index.html`: `lang="fa"` and `dir="rtl"`.
- `tokens.css`: Persian-capable font stack.
- Persian text for headings, labels, hints, buttons, status/role labels and error messages that
  the frontend authors itself.
- Mapping of backend validation messages for `full_name`, `email`, `password` to Persian.
- Directional CSS fixes (`text-align: start`, logical inset properties, no `letter-spacing` on
  Persian text).

### Out of scope

- Backend messages and API error codes (unchanged).
- Other screens (owner application, dashboards, administration).
- A full i18n framework, locale switching, translated URLs, or a language selector.
- Iframes' content, emails, or PDFs.

### Non-goals

- Do not translate the product brand name in the wordmark; it stays `BeautyBook`.
- Do not introduce a translation library or a new runtime dependency.

## 5. Functional requirements

- **FR-1**: The document declares `lang="fa"` and `dir="rtl"`.
- **FR-2**: Every user-visible string on `/login` and `/register` is Persian, except the brand
  wordmark, the email address the user typed, and raw enum values that have a defined Persian
  label.
- **FR-3**: Field labels are associated with their inputs (`<label for>`), so Persian labels keep
  their accessibility relationship.
- **FR-4**: Email and password inputs render their content left to right while their labels and
  surrounding text stay right to left.
- **FR-5**: Status and role values (`active`, `customer`, `salon_owner`, `admin`, and the blocked
  statuses) are displayed through a Persian label map.
- **FR-6**: The font stack prefers a Persian-capable family and falls back to system fonts.
- **FR-7**: No new npm dependency is added.

## 6. Business rules and invariants

- The backend remains authoritative for validation, authorization and state changes.
- Error codes are unchanged; only the displayed text is translated.
- The form never reveals whether an email exists on a failed login beyond the existing generic
  message.
- Accessibility must not regress: labels, `aria-invalid`, `aria-describedby`, `role="alert"` and
  focus management stay intact.

## 7. UX and API behavior

### UI

- Persian copy, right-to-left layout, `text-align: start` for text blocks.
- Persian numerals in user-facing validation text (`۱۲ تا ۱۲۸`).
- Success panels show Persian labels for role and status.

### API

No change. Request and response bodies, codes and status codes are identical.

## 8. Data impact

None. No schema, migration or stored data changes.

## 9. Security and privacy

- No secret or personal data is added to the UI.
- The generic invalid-credentials message stays generic.
- `dir` and `lang` are presentation attributes only.

## 10. Edge cases

- A user's full name may be Latin; the name input stays direction-agnostic (`dir="auto"`).
- Mixed content such as a Persian sentence containing an email must render without breaking the
  sentence order; the email is wrapped in `<strong>`.
- Long Persian words wrap; containers already use `minmax(0, ...)` and `width: min(...)`.
- The brand wordmark stays Latin and must not be flipped.

## 11. Acceptance criteria

### AC-1

`index.html` contains `<html lang="fa" dir="rtl">`.

### AC-2

The login page renders the heading "ورود به بیوتی‌بوک" and no English UI strings.

### AC-3

Empty submission of the login form shows "ایمیل خود را وارد کنید." and "رمز عبور را وارد کنید.".

### AC-4

A wrong password shows "ایمیل یا رمز عبور نادرست است.".

### AC-5

The registration page shows Persian labels and, on success, "خوش آمدید، …" with the role shown as
«مشتری».

### AC-6

A duplicate email shows "حسابی با این ایمیل از قبل وجود دارد" and keeps the link to sign in.

### AC-7

The `#email` input in both forms has `dir="ltr"`.

### AC-8

`tokens.css` defines `--font-sans` with `Vazirmatn` first and Persian-capable fallbacks.

### AC-9

All existing unit tests pass after being updated to the Persian expectations; `npm run typecheck`
and `npm run build` succeed.

## 12. Test strategy

- Unit tests (Vitest + Vue Test Utils) for rendered Persian text, validation messages, backend
  error mapping, and the `dir="ltr"` attribute on Latin inputs.
- A static assertion test that reads `index.html` and `tokens.css` to verify AC-1 and AC-8.
- Manual browser check of `/login` and `/register` for direction, font rendering, focus order and
  the success panels.

## 13. Dependencies and open questions

### Dependencies

- F-001 authentication screens (implemented).

### Open questions

- Whether the whole application should adopt an i18n library later. Deferred; this feature keeps
  copy in components to avoid a dependency without an ADR.

## 14. Decision log

- 2026-11-20: Persian copy is written directly in the components instead of adding `vue-i18n`.
  Reason: one locale, no runtime switching, no new dependency. Trade-off: adding a second locale
  later requires an extraction step.
- 2026-11-20: The font stack uses locally installed or system Persian fonts (Vazirmatn if present,
  then Tahoma/Segoe UI) instead of bundling font files. Reason: no binary assets, no third-party
  CDN, works offline. Trade-off: Vazirmatn only renders for users who installed it.

## 15. Definition of Ready

- Registered in `Task-List.md` as F-019.
- `SPEC.md` and `PLAN.md` exist with testable acceptance criteria.
- No ADR required: no dependency, boundary, persistence or security change.
