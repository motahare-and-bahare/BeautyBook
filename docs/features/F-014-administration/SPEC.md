# SPEC - F-014 Administration, increment 1: administrator user list

**Task:** F-014 (increment 1)
**Module:** `administration`
**Status:** Implemented (2026-11-25)
**Depends on:** F-001 (identity, sessions, roles, `require_roles`)

> Scope note: the owner asked for this increment directly, before the full F-014 administration
> scope (moderation, settings, audit log) was specified. It is read-only and reuses the existing
> role dependency, so it adds no new authorization concept.

---

## 1. Problem

An operator can now create the first administrator with `python -m app.cli create-admin`, but the
platform offers no way to see the accounts that exist. Support and moderation cannot check who is
registered, which roles an account holds, or whether an owner-applicant account is still pending.
The only alternative today is querying the database by hand, which is unauditable and easy to get
wrong.

## 2. Objective

Provide an administrator-only, read-only, paginated list of accounts with their roles and status,
reachable from a `/admin/users` page in the frontend that no other role can open.

## 3. Actors and permissions

| Actor | Allowed | Not allowed |
|---|---|---|
| Public visitor (no session) | Nothing; `401 UNAUTHENTICATED` | Reading any account |
| Customer | Nothing; `403 FORBIDDEN` | Reading any account |
| Salon owner | Nothing; `403 FORBIDDEN` | Reading any account |
| Administrator | Read one page of accounts with roles and status | Any write through this endpoint |
| Frontend guard | Redirect a signed-out visitor to login, a non-admin to `/forbidden` | Making an authorization decision the backend would not make |

The backend role check is authoritative. The router guard only decides which screen to render.

## 4. In scope

- `GET /api/v1/admin/users` with cursor pagination, roles, and status.
- `adminApi.listUsers` wrapper and the auth store that the guard needs.
- `/admin/users` page with loading, empty, success, error, and retry states, plus "load more".
- `/forbidden` (403) page.
- An administrator link from the login success panel to the user list.

## 5. Out of scope

Search and filtering, per-user detail, role grant/revoke, suspend/reactivate, edit or delete,
CSV export, audit-log writes for reads, and any change to identity, sessions, or the schema.

## 6. API contract

```text
GET /api/v1/admin/users?limit=20&cursor=<opaque>

200 {
  "items": [
    {
      "id": "uuid",
      "full_name": "string",
      "email": "string",
      "roles": ["admin", "customer"],
      "status": "active",
      "created_at": "2026-11-25T10:15:30Z"
    }
  ],
  "next_cursor": "opaque-or-null"
}
```

| Case | Response |
|---|---|
| No session | `401 UNAUTHENTICATED` |
| Session without `admin` | `403 FORBIDDEN` |
| `limit` outside 1-100 | `422 VALIDATION_ERROR` |
| Malformed `cursor` | `422 INVALID_CURSOR` |

## 7. Business rules and invariants

1. Ordering is `created_at` descending, then `id` descending. It is total and stable.
2. Pagination is keyset, not offset: a page request never repeats or skips an account, even when
   accounts are created between requests.
3. `next_cursor` is `null` only when there is no further page.
4. `limit` defaults to 20 and is bounded to 1-100.
5. The cursor is opaque and contains only the sort key. It carries no personal data, and an
   unreadable cursor is a client error, never a 500.
6. Roles are read from `user_roles` for every request; a grant or revocation applies immediately.
7. The response never contains `password_hash`, `token_hash`, session identifiers, or
   owner-application content.
8. The endpoint is read-only: no account, role, or session is modified.

## 8. UI behavior

- `/admin/users` requires a session and the `admin` role (`meta.requiresAuth`, `meta.roles`).
- Signed out: redirect to `/login?redirect=/admin/users`.
- Signed in without `admin`: `/forbidden` with a Persian explanation.
- States: loading, empty ("هنوز هیچ کاربری ثبت نشده است."), error with a retry action, success.
- Roles and statuses render through the existing Persian labels, never raw enum values.
- The list shows name, email (LTR), roles, status, and membership date.
- "نمایش کاربران بیشتر" appears only when `next_cursor` is set.

## 9. Data and migration impact

None. The endpoint reads existing tables and no migration is added.

## 10. Security and privacy

- Deny by default: the role dependency runs before the handler and before any query.
- The list is PII-minimal: name, email, roles, status, creation time. Email is required for
  support and identification, so it is included deliberately.
- Logs record the page size and whether more rows exist, never an email or a cursor.
- The cursor is opaque, so it cannot be edited into a role or status filter.
- The frontend never stores the session or credentials; the session stays an HttpOnly cookie.

## 11. Acceptance criteria

| ID | Criterion |
|---|---|
| AC-1 | An administrator receives `200` with the accounts ordered newest first. |
| AC-2 | `roles` contains every role of each account, sorted alphabetically. |
| AC-3 | Walking the cursor returns every account exactly once, including when `limit` is 2. |
| AC-4 | `next_cursor` is `null` on the last page and when fewer than `limit` rows remain. |
| AC-5 | A customer or salon owner receives `403 FORBIDDEN`; no session receives `401`. |
| AC-6 | No response body contains a password hash, a token, or a session id. |
| AC-7 | `limit=0`, `limit=101`, and a malformed cursor return `422` with the documented code. |
| AC-8 | `/admin/users` renders for an admin, redirects a signed-out visitor to login, and shows the 403 page for a customer. |

## 12. Test strategy

- **Unit:** cursor round-trip, offset timezone, naive timestamp, six malformed cursors, limit bounds.
- **Integration (PostgreSQL):** ordering, roles, pagination without duplicates, default page size,
  `401`/`403`, invalid cursor, `limit` bounds, secrets absent, immediate role visibility.
- **Frontend unit:** list rendering with Persian labels, empty state, error plus retry, load-more
  with the server cursor, no load-more on the last page, and the three guard outcomes.

## 13. Open questions

- Should the list support search, status, or role filters? Deferred to a later F-014 increment.
- Should reading the user list write an audit record? Auditing is part of F-014; reads of PII are
  a candidate, but the audit storage is not specified yet.
