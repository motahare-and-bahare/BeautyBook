"""Identity use cases.

These functions flush but do not commit on their own; the public use case owns the transaction.
For customer registration that means the user, the role, and the session either all become
visible together or not at all. Clock, lifetime, token factory, hasher, and password hasher are
injectable for deterministic tests.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    password_needs_rehash,
    verify_password,
)
from app.modules.identity import repository
from app.modules.identity.domain import (
    Role,
    UserStatus,
    can_authenticate,
    normalize_email,
    normalize_full_name,
    session_is_valid,
    validate_password,
)
from app.modules.identity.models import AuthSession, User

logger = logging.getLogger(__name__)


class SessionInvalidError(Exception):
    """The session cannot authenticate the request.

    ``reason`` is for internal logs only. The HTTP layer maps every case to the same
    ``401 UNAUTHENTICATED`` response.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"session rejected: {reason}")
        self.reason = reason


class SessionNotAllowedError(Exception):
    """A session may only be created for an active account."""


class EmailAlreadyRegisteredError(Exception):
    """The normalized email already belongs to an account in either registration flow."""


class InvalidCredentialsError(Exception):
    """The email is unknown or the password is wrong.

    The HTTP layer maps every case to the same ``401 INVALID_CREDENTIALS`` response so an
    attacker cannot tell which one failed.
    """


class AccountNotActiveError(Exception):
    """The password was correct, but the account may not sign in.

    ``status`` is safe to expose only because the password has already been verified.
    """

    def __init__(self, status: UserStatus) -> None:
        super().__init__(f"account is not active: {status.value}")
        self.status = status


@dataclass(frozen=True, slots=True)
class CustomerRegistration:
    """The result of a successful customer registration."""

    user: User
    auth_session: AuthSession
    raw_session_token: str
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AdminBootstrap:
    """The result of the first-administrator bootstrap command."""

    user: User
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Login:
    """The result of a successful login."""

    user: User
    auth_session: AuthSession
    raw_session_token: str
    roles: tuple[str, ...]


_BLOCKED_LOGIN_EVENTS: dict[UserStatus, str] = {
    UserStatus.PENDING_APPROVAL: "login_blocked_pending",
    UserStatus.REJECTED: "login_blocked_rejected",
    UserStatus.SUSPENDED: "login_blocked_suspended",
}


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    """A real Argon2id digest used to burn comparable time for unknown emails."""

    return hash_password("beautybook-unknown-email-dummy-password")


def _parse_status(value: str) -> UserStatus | None:
    try:
        return UserStatus(value)
    except ValueError:
        return None


def create_session_for_user(
    session: Session,
    user: User,
    *,
    now: datetime | None = None,
    ttl_days: int | None = None,
    token_factory: Callable[[], str] = generate_session_token,
    token_hasher: Callable[[str], str] = hash_session_token,
) -> tuple[AuthSession, str]:
    """Create a session for an active user and return it with the raw token.

    The raw token is never stored; only its SHA-256 digest is persisted.
    """

    status = _parse_status(user.status)
    if status is None or not can_authenticate(status):
        logger.warning("session_refused reason=inactive_account user_id=%s", user.id)
        raise SessionNotAllowedError("only active accounts may hold a session")

    issued_at = now or datetime.now(UTC)
    lifetime_days = ttl_days if ttl_days is not None else get_settings().session_ttl_days
    raw_token = token_factory()

    auth_session = repository.create_session(
        session,
        user_id=user.id,
        token_hash=token_hasher(raw_token),
        expires_at=issued_at + timedelta(days=lifetime_days),
    )
    logger.info("session_created user_id=%s", user.id)
    return auth_session, raw_token


def resolve_session(
    session: Session,
    raw_token: str,
    *,
    now: datetime | None = None,
    token_hasher: Callable[[str], str] = hash_session_token,
) -> tuple[AuthSession, User]:
    """Resolve a raw cookie token to its session and user, or raise ``SessionInvalidError``."""

    checked_at = now or datetime.now(UTC)
    auth_session = repository.get_session_by_token_hash(session, token_hasher(raw_token))

    if auth_session is None:
        logger.info("session_rejected reason=unknown")
        raise SessionInvalidError("unknown")

    user = repository.get_user_by_id(session, auth_session.user_id)
    if user is None:
        logger.warning("session_rejected reason=missing_user session_id=%s", auth_session.id)
        raise SessionInvalidError("missing_user")

    status = _parse_status(user.status)
    if status is None or not session_is_valid(
        expires_at=auth_session.expires_at,
        revoked_at=auth_session.revoked_at,
        user_status=status,
        now=checked_at,
    ):
        if auth_session.revoked_at is not None:
            reason = "revoked"
        elif auth_session.expires_at <= checked_at:
            reason = "expired"
        else:
            reason = "inactive_account"
        logger.info(
            "session_rejected reason=%s session_id=%s user_id=%s",
            reason,
            auth_session.id,
            user.id,
        )
        raise SessionInvalidError(reason)

    return auth_session, user


def revoke_session(
    session: Session,
    auth_session: AuthSession,
    *,
    now: datetime | None = None,
) -> None:
    """Revoke one session without affecting the user's other sessions."""

    repository.revoke_session(
        session,
        auth_session,
        revoked_at=now or datetime.now(UTC),
    )
    logger.info("session_revoked session_id=%s", auth_session.id)


def _is_duplicate_email(error: IntegrityError) -> bool:
    """Tell an email collision apart from other integrity failures.

    psycopg exposes the violated constraint name on ``orig.diag``. SQLite only reports the
    table and column in the exception message, so the message is used as a fallback rather than
    turning a duplicate registration into a 500 on SQLite.
    """

    diag = getattr(error.orig, "diag", None)
    constraint_name = getattr(diag, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_users_email"

    message = str(error.orig).lower()
    return "users.email" in message and ("unique" in message or "duplicate" in message)


def register_customer(
    session: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    now: datetime | None = None,
    password_hasher: Callable[[str], str] = hash_password,
    token_factory: Callable[[], str] = generate_session_token,
    token_hasher: Callable[[str], str] = hash_session_token,
) -> CustomerRegistration:
    """Create an active customer, assign the customer role, and start a session atomically.

    The service owns the single commit. Any failure rolls the whole transaction back, so a
    partially created account can never exist. A concurrent duplicate is caught by the unique
    email constraint and reported as ``EmailAlreadyRegisteredError`` rather than leaking a
    database error.
    """

    cleaned_name = normalize_full_name(full_name)
    normalized_email = normalize_email(email)
    validate_password(password)

    if repository.get_user_by_email(session, normalized_email) is not None:
        logger.info("customer_registration_rejected reason=duplicate_email")
        raise EmailAlreadyRegisteredError

    try:
        user = repository.create_user(
            session,
            full_name=cleaned_name,
            email=normalized_email,
            password_hash=password_hasher(password),
            status=UserStatus.ACTIVE.value,
        )
        repository.add_role(session, user_id=user.id, role=Role.CUSTOMER)
        auth_session, raw_token = create_session_for_user(
            session,
            user,
            now=now,
            token_factory=token_factory,
            token_hasher=token_hasher,
        )
        roles = tuple(repository.list_roles(session, user.id))
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_duplicate_email(error):
            logger.info("customer_registration_rejected reason=duplicate_email")
            raise EmailAlreadyRegisteredError from error
        raise
    except Exception:
        session.rollback()
        raise

    logger.info("customer_registered user_id=%s", user.id)
    return CustomerRegistration(
        user=user,
        auth_session=auth_session,
        raw_session_token=raw_token,
        roles=roles,
    )


def create_admin(
    session: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    password_hasher: Callable[[str], str] = hash_password,
) -> AdminBootstrap:
    """Create an active administrator with the ``admin`` and ``customer`` roles.

    This is the only path that creates an administrator without an existing administrator, and it
    is reachable only from the administrative CLI, never from HTTP. Validation reuses the same
    domain rules as registration, and the user plus both role rows are written in one commit, so
    an interrupted run cannot leave a half-created account behind.
    """

    cleaned_name = normalize_full_name(full_name)
    normalized_email = normalize_email(email)
    validate_password(password)

    if repository.get_user_by_email(session, normalized_email) is not None:
        logger.info("admin_bootstrap_rejected reason=duplicate_email")
        raise EmailAlreadyRegisteredError

    try:
        user = repository.create_user(
            session,
            full_name=cleaned_name,
            email=normalized_email,
            password_hash=password_hasher(password),
            status=UserStatus.ACTIVE.value,
        )
        repository.add_role(session, user_id=user.id, role=Role.ADMIN)
        repository.add_role(session, user_id=user.id, role=Role.CUSTOMER)
        roles = tuple(repository.list_roles(session, user.id))
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if _is_duplicate_email(error):
            logger.info("admin_bootstrap_rejected reason=duplicate_email")
            raise EmailAlreadyRegisteredError from error
        raise
    except Exception:
        session.rollback()
        raise

    logger.info("admin_bootstrapped user_id=%s", user.id)
    return AdminBootstrap(user=user, roles=roles)


def login(
    session: Session,
    *,
    email: str,
    password: str,
    now: datetime | None = None,
    current_session_token: str | None = None,
    password_hasher: Callable[[str], str] = hash_password,
    password_verifier: Callable[[str, str], bool] = verify_password,
    password_rehash_checker: Callable[[str], bool] = password_needs_rehash,
    token_factory: Callable[[], str] = generate_session_token,
    token_hasher: Callable[[str], str] = hash_session_token,
) -> Login:
    """Verify credentials, enforce account status, and start a fresh session.

    The use case owns the single commit. A failed attempt changes nothing. For an unknown email a
    dummy hash verification still runs, so the response time does not reveal whether an account
    exists. Account status is only inspected after the password succeeds.

    If the request carries a session belonging to the same user, it is revoked and replaced
    (session rotation); other sessions stay valid.
    """

    normalized_email = normalize_email(email)
    checked_at = now or datetime.now(UTC)
    user = repository.get_user_by_email(session, normalized_email)

    if user is None:
        # Burn the same Argon2 work as a real verification before failing generically.
        password_verifier(password, _dummy_password_hash())
        logger.info("login_failure reason=invalid_credentials")
        raise InvalidCredentialsError

    if not password_verifier(password, user.password_hash):
        logger.info("login_failure reason=invalid_credentials user_id=%s", user.id)
        raise InvalidCredentialsError

    status = _parse_status(user.status)
    if status is None:
        logger.warning("login_blocked_unknown_status user_id=%s", user.id)
        raise InvalidCredentialsError

    if not can_authenticate(status):
        event = _BLOCKED_LOGIN_EVENTS[status]
        logger.info("%s user_id=%s", event, user.id)
        raise AccountNotActiveError(status)

    try:
        if password_rehash_checker(user.password_hash):
            user.password_hash = password_hasher(password)
            session.flush()
            logger.info("password_rehashed user_id=%s", user.id)

        if current_session_token:
            existing = repository.get_session_by_token_hash(
                session,
                token_hasher(current_session_token),
            )
            if existing is not None and existing.user_id == user.id and existing.revoked_at is None:
                repository.revoke_session(session, existing, revoked_at=checked_at)
                logger.info("session_rotated user_id=%s session_id=%s", user.id, existing.id)

        auth_session, raw_token = create_session_for_user(
            session,
            user,
            now=checked_at,
            token_factory=token_factory,
            token_hasher=token_hasher,
        )
        roles = tuple(repository.list_roles(session, user.id))
        session.commit()
    except Exception:
        session.rollback()
        raise

    logger.info("login_success user_id=%s", user.id)
    return Login(
        user=user,
        auth_session=auth_session,
        raw_session_token=raw_token,
        roles=roles,
    )
