# ADR-0010: Registration Flows, Role Assignment, and Administrator Provisioning

- **Status:** Accepted - 2026-11-18, approved together with the F-001 SPEC and PLAN
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent
- **Revision:** 2. Supersedes the earlier "public signup creates customers only" proposal. That
  version was never accepted and never implemented.

## Context

BeautyBook has three roles: customer, salon owner, and administrator. They have different levels of
trust:

- a customer uses the marketplace;
- a salon owner operates a business and must be accountable;
- an administrator can change platform state and must never be self-service.

The first proposal made all public registration create a customer, then granted the salon-owner
role later through an onboarding flow. The project owner has decided on a different product model:
two explicit, separate registration journeys, with the salon-owner journey gated by administrator
approval.

The system needs to answer four questions without ambiguity:

1. Which roles can a public visitor obtain?
2. When does a salon owner become "approved"?
3. How is the first administrator created?
4. How are later administrators created?

## Decision

### Two public registration flows, no public administrator registration

| Flow | Route | Who it is for | Result |
|---|---|---|---|
| Customer registration | `/register` -> `POST /api/v1/auth/register/customer` | People who want to browse and book | Active account, `customer` role, signed in immediately |
| Salon-owner registration | `/register/owner` -> `POST /api/v1/auth/register/owner` | People who want to operate a salon | `pending_approval` account and a pending salon application; no session, no `salon_owner` role |
| Administrator | No public route | Platform operators | Created only out-of-band or by an existing administrator |

- Each flow has its own endpoint and its own form. There is **no role selector** and no shared
  `role` field. The endpoint determines the outcome.
- Both request schemas reject unknown fields such as `role`, `id`, `status`, and `is_active`.
- An email address identifies at most one account across both flows. A visitor who already has an
  account cannot create a second one through the owner form; applying as an existing customer is a
  later feature (F-004).

### Salon-owner approval

- Salon-owner registration creates:
  - a `users` row with `status = pending_approval`,
  - an `owner_applications` row with `status = pending`, containing the personal data already in
    `users` plus the submitted salon basics (salon name, city, phone, timezone, currency, optional
    description).
- It does **not** create a session and does **not** grant the `salon_owner` role. The role is
  granted only by an administrator's approval, in the same transaction that activates the account.
- A pending or rejected account cannot sign in. The specific reason is returned only after the
  password has been verified, so it is not an account-enumeration oracle.
- Approval unlocks the salon dashboard placeholder. It does **not** publish a salon. Publishing and
  the full salon profile are F-004.
- Rejection requires a reason, which is stored for support. Re-application in F-001 is not
  supported; it is handled by administration later.

### Administrator provisioning

- **First administrator:** a local CLI command (`python -m app.cli create-admin`) run by an operator
  with database access. It reads the password interactively or from standard input, never from a
  command-line argument or a committed environment file.
- **Later administrators:** an existing administrator grants the `admin` role to an existing
  active user through an administrator-only endpoint. There is no open "create admin" endpoint.
- The administrator role is stored in `user_roles` like any other role, but the only paths that can
  write it are the CLI and the administrator-only grant endpoint.
- Role removal, "last administrator" protection, and full user administration are F-014. F-001
  implements grant only and documents the gap.

### Why the role is granted at approval, not at registration

Granting `salon_owner` at registration would mean the role no longer proves that anyone reviewed
the business. Keeping the role empty until approval makes the invariant simple: **if the role
exists, the account was approved**. This also prevents a pending account from being treated as an
owner by any future endpoint that checks only the role.

## Alternatives considered

1. **One form with a role selector (Customer / Salon Owner).** Rejected: it invites escalation, is
   easy to mass-assign by mistake, and blurs "wants to be an owner" with "is approved".
2. **One form, then a separate "become an owner" request after signup.** This is what the earlier
   proposal implied. It is good for existing customers, but the project owner wants a dedicated
   owner journey with salon information collected up front. The existing-customer path remains a
   later F-004 feature.
3. **Assign `salon_owner` immediately and gate only the UI.** Rejected: the role would stop being a
   trustworthy authorization signal, and any endpoint checking only the role would leak access.
4. **Invitation-only registration.** Safer but adds an invitation system before the onboarding need
   is proven. Deferred.
5. **Seed the first admin from an environment variable.** Rejected: risks committed credentials and
   awkward rotation. A documented one-time operational command is preferred.
6. **Allow administrators to be created through a public "admin signup" protected by a secret
   link.** Rejected: a secret URL is a credential that leaks easily and cannot be audited well.

## Consequences

Positive:

- The three roles now have three visibly different trust paths.
- A pending owner cannot obtain a session or an owner role, so the approval gate is enforced by the
  data model, not only by the UI.
- Administrator creation is deliberate and auditable.
- The customer journey stays short: register, signed in, browsing.

Negative and risks:

- F-001 grows: it now includes an owner application table, administrator review endpoints, a
  minimal review page, and administrator bootstrap.
- A salon owner cannot start work in one step; approval is a required human step.
- The first administrator needs an operational step before any real deployment.
- Rejected applicants need a support path that F-001 does not provide.
- Full role management, revocation, and audit persistence are deferred to F-014; F-001 logs
  privileged actions but does not yet store them in an audit table.

## Verification

- `POST /auth/register/customer` creates an active customer with a session.
- `POST /auth/register/owner` returns `202`, creates no session, and grants no `salon_owner` role.
- The pending owner cannot log in and receives `ACCOUNT_PENDING_APPROVAL` only with a correct
  password.
- An administrator approval activates the account and grants `salon_owner` atomically.
- A rejection stores a reason and leaves the account unable to sign in.
- A second approval of the same application returns `409`, and two concurrent approvals produce
  exactly one success.
- A customer calling an administrator endpoint receives `403`.
- `"role": "admin"` in either registration request is rejected by schema validation.
- The first administrator can be created by the CLI; the same email cannot be created twice.
- No public endpoint can create an administrator account from scratch.

## References

- `docs/features/F-001-authentication/SPEC.md`, Sections 2, 3, 5, and 8.
- `docs/features/F-001-authentication/PLAN.md`, Steps 6, 7, and 11-14.
- `docs/adr/0009-authorization-model.md`.
- `docs/SRS.md`, FR-IAM-001 to FR-IAM-011, FR-SAL-001, FR-ADM-001 to FR-ADM-005.
