"""Identity HTTP endpoints.

The CSRF bootstrap, customer registration, login, and current-user lookup are implemented in this
step. Owner applications, logout, and the administrator endpoints follow in later steps.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import generate_csrf_token
from app.infrastructure.database import get_session
from app.modules.identity import service
from app.modules.identity.dependencies import (
    CurrentUserDep,
    require_csrf,
    set_csrf_cookie,
    set_session_cookie,
)
from app.modules.identity.domain import DomainValidationError, UserStatus
from app.modules.identity.models import User
from app.modules.identity.schemas import LoginRequest, RegisterCustomerRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DatabaseSession = Annotated[Session, Depends(get_session)]

EMAIL_ALREADY_REGISTERED_CODE = "EMAIL_ALREADY_REGISTERED"
VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
INVALID_CREDENTIALS_CODE = "INVALID_CREDENTIALS"

_BLOCKED_ACCOUNT_RESPONSES: dict[UserStatus, tuple[str, str]] = {
    UserStatus.PENDING_APPROVAL: (
        "ACCOUNT_PENDING_APPROVAL",
        "Your account is still under review. You can sign in after approval.",
    ),
    UserStatus.REJECTED: (
        "ACCOUNT_REJECTED",
        "This account was not approved. Contact support if you think this is a mistake.",
    ),
    UserStatus.SUSPENDED: (
        "ACCOUNT_SUSPENDED",
        "This account is suspended. Contact support for help.",
    ),
}


@router.get("/csrf")
def issue_csrf_token(response: Response) -> dict[str, str]:
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return {"csrf_token": token}


@router.post(
    "/register/customer",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
def register_customer(
    payload: RegisterCustomerRequest,
    response: Response,
    session: DatabaseSession,
) -> UserResponse:
    """Create an active customer and sign them in immediately.

    The service performs one atomic commit. A duplicate email is a client conflict, not a server
    error, and the response never includes a hash or token.
    """

    try:
        registration = service.register_customer(
            session,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
        )
    except service.EmailAlreadyRegisteredError as error:
        raise AppError(
            EMAIL_ALREADY_REGISTERED_CODE,
            "An account with this email already exists. Sign in instead.",
            409,
        ) from error
    except DomainValidationError as error:
        raise AppError(
            VALIDATION_ERROR_CODE,
            "The request contains invalid values.",
            422,
            {error.field or "body": error.message},
        ) from error

    _start_session(response, registration.raw_session_token)
    return _user_response(registration.user, registration.roles)


@router.post(
    "/login",
    response_model=UserResponse,
    dependencies=[Depends(require_csrf)],
)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    session: DatabaseSession,
) -> UserResponse:
    """Verify credentials and start a new session for an active account.

    Unknown emails and wrong passwords return the same 401 body. Pending, rejected, and suspended
    accounts receive a status-specific 403 only after the password has been verified. The existing
    cookie, when it belongs to the same user, is rotated out.
    """

    settings = get_settings()
    current_token = request.cookies.get(settings.session_cookie_name)

    try:
        result = service.login(
            session,
            email=payload.email,
            password=payload.password,
            current_session_token=current_token,
        )
    except service.InvalidCredentialsError as error:
        raise AppError(
            INVALID_CREDENTIALS_CODE,
            "Invalid email or password.",
            401,
        ) from error
    except service.AccountNotActiveError as error:
        code, message = _BLOCKED_ACCOUNT_RESPONSES[error.status]
        raise AppError(code, message, 403) from error
    except DomainValidationError as error:
        raise AppError(
            VALIDATION_ERROR_CODE,
            "The request contains invalid values.",
            422,
            {error.field or "body": error.message},
        ) from error

    _start_session(response, result.raw_session_token)
    return _user_response(result.user, result.roles)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUserDep) -> UserResponse:
    """Return the signed-in user, with roles and status read from the database.

    The dependency rejects a missing, unknown, expired, revoked, or non-active session with
    ``401 UNAUTHENTICATED``. This endpoint has no CSRF requirement because it changes nothing.
    """

    return _user_response(current_user.user, current_user.roles)


def _start_session(response: Response, raw_session_token: str) -> None:
    """Issue the session cookie and rotate the readable CSRF token."""

    set_session_cookie(response, raw_session_token)
    set_csrf_cookie(response, generate_csrf_token())


def _user_response(user: User, roles: tuple[str, ...]) -> UserResponse:
    """Map a user row to the safe public schema. Secrets never enter this shape."""

    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        roles=list(roles),
        status=user.status,
        created_at=user.created_at,
    )
