# ADR-0009: Role and Ownership Authorization Model

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook has three primary roles: customer, salon owner, and administrator. A simple role check
is not enough:

- two salon owners must not read or modify each other's salon, services, images, hours, or
  bookings;
- two customers must not read each other's bookings;
- an administrator may have broad access, but privileged actions must be explicit and audited;
- a user might legitimately hold more than one role over time (for example, a customer who later
  opens a salon).

The authorization design affects every endpoint, query, and test. Retrofitting ownership checks is
expensive and error-prone.

## Decision

Use **role-based access control plus resource ownership checks**:

- Store roles in a `user_roles` join table (`customer`, `salon_owner`, `admin`). The schema supports
  multiple roles per user even if the MVP UI presents one primary role.
- A salon has an `owner_user_id`. Every owner operation resolves the salon from the authenticated
  user, never from a client-supplied owner ID.
- Every protected use case performs:
  1. authentication,
  2. role permission check,
  3. resource ownership or explicit administrative permission check,
  4. domain validation.
- Deny by default. Unknown role/permission combinations are rejected.
- Administrators receive explicit capabilities. Administrative actions that change accounts,
  salons, bookings, or settings require a reason and an audit record.
- Frontend route guards are a UX convenience only; the backend repeats every check.
- Authorization failures return `403` for authenticated-but-forbidden requests and do not reveal
  whether another tenant's resource exists (`404` where appropriate).

## Alternatives considered

1. **Single `role` column on `users`.** Simpler, but makes dual roles and future staff permissions
   awkward. Rejected for the baseline, though `identity` and `users` may still merge modules.
2. **A full policy engine (for example, OPA/Cedar).** Rejected: too much operational and conceptual
   overhead for three roles and ownership rules.
3. **UI-only role checks.** Rejected: trivially bypassed.
4. **Global administrator bypass without audit.** Rejected: violates least privilege and
   accountability.

## Consequences

Positive:

- Clear, testable security boundary.
- Supports dual roles without a schema rewrite.
- Ownership checks are explicit in use cases.
- Administrative actions are accountable.

Negative and risks:

- Every new endpoint must remember the ownership check; tests are mandatory.
- More queries in some use cases; load only what is needed.
- A future staff model will need finer-grained permissions and a new ADR.
- Role changes require session/permission refresh behavior to be defined.

## Relationship to registration and approval

ADR-0010 defines how roles come into existence. This ADR defines what a role allows once it
exists. The two are complementary:

- A **customer** account is active immediately.
- The **salon_owner** role is granted only by administrator approval or an administrator grant, so
  its presence is evidence that the business was reviewed.
- The **admin** role is never available through public registration.

Therefore an owner endpoint may safely require `salon_owner`, but it must still resolve the salon
from the authenticated user and check ownership. Neither role nor approval replaces the ownership
check.

## Verification

- A customer cannot read or cancel another customer's booking.
- An owner cannot read or edit another salon's profile, services, images, hours, or bookings.
- A customer cannot call owner or admin endpoints.
- An owner cannot call admin endpoints.
- An administrator action creates an audit record with actor, target, reason, and timestamp.
- Missing/invalid authentication returns `401`; authenticated but forbidden returns `403`.

## References

- `docs/SRS.md`, FR-IAM-007, FR-SAL-007, FR-SVC-007, BR-001 to BR-003.
- `docs/ARCHITECTURE.md`, Section 9.
- `AGENTS.md`, Sections 9 and 11.
