"""Request dependencies shared by identity endpoints.

This module owns the authentication boundary: it resolves the opaque session cookie to a
database-backed user, loads roles from the database on every request, and exposes a reusable
role gate. Authorization is always enforced here or in a service, never only in the UI.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import tokens_match
from app.infrastructure.database import get_session
from app.modules.identity import repository, service
from app.modules.identity.domain import Role
from app.modules.identity.models import User

logger = logging.getLogger(__name__)

CSRF_INVALID_CODE = "CSRF_INVALID"
UNAUTHENTICATED_CODE = "UNAUTHENTICATED"
FORBIDDEN_CODE = "FORBIDDEN"

SessionDep = Annotated[Session, Depends(get_session)]


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """The authenticated caller and the roles read from the database for this request."""

    user: User
    roles: tuple[str, ...]


def get_current_user(request: Request, session: SessionDep) -> CurrentUser:
    """Resolve the session cookie to an active user, or raise a generic 401.

    The raw token is never logged. Every failure reason (missing, unknown, expired, revoked,
    non-active account) maps to the same public response so an attacker cannot probe sessions.
    """

    settings = get_settings()
    raw_token = request.cookies.get(settings.session_cookie_name)

    if not raw_token:
        logger.info("session_rejected reason=missing")
        raise AppError(
            UNAUTHENTICATED_CODE,
            "Authentication is required.",
            401,
        )

    try:
        _, user = service.resolve_session(session, raw_token)
    except service.SessionInvalidError as error:
        raise AppError(
            UNAUTHENTICATED_CODE,
            "Authentication is required.",
            401,
        ) from error

    roles = tuple(repository.list_roles(session, user.id))
    return CurrentUser(user=user, roles=roles)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role | str) -> Callable[[CurrentUser], CurrentUser]:
    """Build a dependency that allows a caller holding at least one of ``roles``.

    The role list is validated while the route is being wired, so a typo fails at startup rather
    than silently denying every request. Roles are re-read from the database for each request, so
    a grant or revocation applies immediately.
    """

    required = frozenset(_role_value(role) for role in roles)
    if not required:
        raise ValueError("require_roles needs at least one role")

    def dependency(current_user: CurrentUserDep) -> CurrentUser:
        if required.isdisjoint(current_user.roles):
            logger.warning(
                "authorization_denied required=%s user_id=%s",
                ",".join(sorted(required)),
                current_user.user.id,
            )
            raise AppError(
                FORBIDDEN_CODE,
                "You do not have permission to perform this action.",
                403,
            )
        return current_user

    return dependency


def _role_value(role: Role | str) -> str:
    try:
        return Role(role).value
    except ValueError as error:
        raise ValueError(f"unknown role: {role!r}") from error


def require_csrf(request: Request) -> None:
    """Reject a state-changing request unless the cookie and header agree.

    The check runs as a dependency, before the handler and before any database access.
    Tokens are never logged.
    """

    settings = get_settings()
    expected = request.cookies.get(settings.csrf_cookie_name)
    provided = request.headers.get(settings.csrf_header_name)

    if not tokens_match(expected, provided):
        logger.warning("csrf_rejected path=%s", request.url.path)
        raise AppError(
            CSRF_INVALID_CODE,
            "The CSRF token is missing or invalid.",
            403,
        )


def set_csrf_cookie(response: Response, token: str) -> None:
    """Set the double-submit cookie.

    The cookie must be readable by JavaScript so the client can copy it into the header, and it
    must share the session lifetime. ``Secure`` follows the environment.
    """

    settings = get_settings()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


def set_session_cookie(response: Response, raw_token: str) -> None:
    """Set the opaque session token in an ``HttpOnly`` cookie.

    JavaScript can never read this cookie; the browser sends it automatically. The server stores
    only the SHA-256 hash of ``raw_token``.
    """

    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
