"""Session repository and service behavior against PostgreSQL."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_session_token
from app.modules.identity.domain import UserStatus
from app.modules.identity.models import AuthSession, User
from app.modules.identity.service import (
    SessionInvalidError,
    SessionNotAllowedError,
    create_session_for_user,
    resolve_session,
    revoke_session,
)

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
PASSWORD_HASH = "argon2id$v=19$m=65536,t=3,p=4$placeholder$placeholder"


def make_user(
    email: str = "session-user@example.com",
    status: str = UserStatus.ACTIVE.value,
) -> User:
    return User(full_name="Session User", email=email, password_hash=PASSWORD_HASH, status=status)


def test_only_the_sha256_hash_of_the_token_is_stored(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    auth_session, raw_token = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    stored_hash = db_session.scalar(select(AuthSession.token_hash))
    assert stored_hash == hash_session_token(raw_token)
    assert stored_hash is not None
    assert stored_hash != raw_token
    assert len(stored_hash) == 64
    assert auth_session.token_hash == stored_hash


def test_a_session_can_be_resolved_by_its_raw_token(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    auth_session, raw_token = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    resolved, resolved_user = resolve_session(db_session, raw_token, now=NOW)

    assert resolved.id == auth_session.id
    assert resolved_user.id == user.id


def test_an_unknown_token_is_rejected(db_session: Session) -> None:
    with pytest.raises(SessionInvalidError):
        resolve_session(db_session, "not-a-real-token", now=NOW)


def test_an_expired_session_is_rejected(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    _, raw_token = create_session_for_user(
        db_session,
        user,
        now=NOW - timedelta(days=8),
        ttl_days=7,
    )
    db_session.commit()

    with pytest.raises(SessionInvalidError):
        resolve_session(db_session, raw_token, now=NOW)


def test_a_revoked_session_is_rejected(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    auth_session, raw_token = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    revoke_session(db_session, auth_session, now=NOW)
    db_session.commit()

    with pytest.raises(SessionInvalidError):
        resolve_session(db_session, raw_token, now=NOW)


def test_revoking_one_session_keeps_other_sessions_valid(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    first, first_token = create_session_for_user(db_session, user, now=NOW)
    _, second_token = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    revoke_session(db_session, first, now=NOW)
    db_session.commit()

    with pytest.raises(SessionInvalidError):
        resolve_session(db_session, first_token, now=NOW)

    resolved, _ = resolve_session(db_session, second_token, now=NOW)
    assert resolved.revoked_at is None


def test_a_user_may_hold_multiple_active_sessions(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    _, first_token = create_session_for_user(db_session, user, now=NOW)
    _, second_token = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    assert first_token != second_token
    assert resolve_session(db_session, first_token, now=NOW)[0].id
    assert resolve_session(db_session, second_token, now=NOW)[0].id


@pytest.mark.parametrize(
    "status",
    [UserStatus.PENDING_APPROVAL, UserStatus.REJECTED, UserStatus.SUSPENDED],
)
def test_a_session_is_never_created_for_a_non_active_user(
    db_session: Session,
    status: UserStatus,
) -> None:
    user = make_user(status=status.value)
    db_session.add(user)
    db_session.flush()

    with pytest.raises(SessionNotAllowedError):
        create_session_for_user(db_session, user, now=NOW)

    assert db_session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_clock_ttl_and_hasher_are_injectable(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    fixed_hash = "f" * 64

    auth_session, raw_token = create_session_for_user(
        db_session,
        user,
        now=NOW,
        ttl_days=1,
        token_factory=lambda: "fixed-raw-token",
        token_hasher=lambda _: fixed_hash,
    )
    db_session.commit()

    assert raw_token == "fixed-raw-token"
    assert auth_session.expires_at == NOW + timedelta(days=1)
    assert auth_session.token_hash == fixed_hash

    resolved, _ = resolve_session(
        db_session,
        raw_token,
        now=NOW,
        token_hasher=lambda _: fixed_hash,
    )
    assert resolved.id == auth_session.id


def test_revocation_is_idempotent(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    auth_session, _ = create_session_for_user(db_session, user, now=NOW)
    db_session.commit()

    revoke_session(db_session, auth_session, now=NOW)
    revoke_session(db_session, auth_session, now=NOW + timedelta(minutes=1))
    db_session.commit()

    assert auth_session.revoked_at == NOW
