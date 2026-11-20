# ADR-0005: Browser Authentication and Session Strategy

- **Status:** Accepted - 2026-11-18, approved together with the F-001 SPEC and PLAN
- **Date:** 2026-11-18
- **Decision owners:** BeautyBook project owner and engineering agent

## Context

BeautyBook is a browser-first application with three roles. It needs secure sign-in, sign-out,
session revocation, password reset, and protection against common browser threats.

The main options are:

1. server-side sessions identified by a cookie,
2. stateless access tokens plus refresh tokens,
3. a hybrid.

The wrong choice is expensive to change later because it affects every protected request, the
frontend client, CSRF handling, and logout behavior.

## Decision

Adopt **database-backed server-side sessions** with a secure cookie:

- Argon2id password hashing via a maintained library.
- A random session identifier stored in an `HttpOnly`, `Secure`, `SameSite=Lax` cookie.
- Only a hash of the session token is stored in the database.
- Session expiry and idle timeout are explicit.
- Sign-out revokes the session.
- Password change revokes other sessions.
- CSRF token required for state-changing requests.
- Email verification required before sensitive actions.
- Rate limiting on register, login, and password reset.
- Password-reset and email-verification tokens are short-lived, single-use, and stored hashed.

This decision is **Accepted**. F-001 implements it and pins the concrete libraries: `argon2-cffi`
for password hashing, `secrets.token_urlsafe(32)` for session tokens, SHA-256 for token storage,
and PostgreSQL-backed sessions. Email verification and rate limiting remain deferred to F-003, but
F-001 is not exposed publicly until those controls exist.

## Alternatives considered

1. **JWT access token in `localStorage`.** Rejected as the default: long-lived credentials in
   JavaScript-accessible storage increase XSS impact, and revocation is harder.
2. **Short-lived JWT access token + refresh token in `HttpOnly` cookie.** Viable, but adds token
   rotation, reuse detection, and revocation complexity that the first release does not need.
3. **Third-party identity provider.** Rejected for the first release: adds an external dependency
   and account-mapping complexity before the core product is proven.

## Consequences

Positive:

- Simple revocation and logout.
- Credentials are not readable by JavaScript.
- Server-side session state is available for auditing and admin suspension.
- Fits a browser-first marketplace.

Negative and risks:

- Requires CSRF protection for cookie-authenticated writes.
- Requires a session table and cleanup of expired sessions.
- Horizontal scaling requires shared session storage; PostgreSQL already provides it.
- Mobile/native clients would need a different flow later.

## Security requirements

- No session token or password in logs.
- Cookie `Secure` in production; `HttpOnly` always.
- `SameSite=Lax` unless a documented cross-site flow requires otherwise.
- Rotate the session identifier on sign-in and privilege change.
- Limit session lifetime and provide "sign out everywhere".
- Test CSRF rejection, session fixation, expired sessions, and revoked sessions.

## References

- `docs/ARCHITECTURE.md`, Section 9.
- `docs/SRS.md`, FR-IAM-001 to FR-IAM-011.
- `AGENTS.md`, Section 11.
