"""Session validity policy and session-token hashing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import generate_session_token, hash_session_token
from app.modules.identity.domain import UserStatus, session_is_valid

EXPIRES_AT = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)


def test_an_active_user_with_a_future_session_is_valid() -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=None,
            user_status=UserStatus.ACTIVE,
            now=EXPIRES_AT - timedelta(hours=1),
        )
        is True
    )


def test_a_session_is_valid_one_microsecond_before_expiry() -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=None,
            user_status=UserStatus.ACTIVE,
            now=EXPIRES_AT - timedelta(microseconds=1),
        )
        is True
    )


def test_a_session_is_invalid_exactly_at_expiry() -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=None,
            user_status=UserStatus.ACTIVE,
            now=EXPIRES_AT,
        )
        is False
    )


def test_a_session_is_invalid_after_expiry() -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=None,
            user_status=UserStatus.ACTIVE,
            now=EXPIRES_AT + timedelta(seconds=1),
        )
        is False
    )


def test_a_revoked_session_is_invalid_even_before_expiry() -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=EXPIRES_AT - timedelta(minutes=5),
            user_status=UserStatus.ACTIVE,
            now=EXPIRES_AT - timedelta(minutes=1),
        )
        is False
    )


@pytest.mark.parametrize(
    "status",
    [UserStatus.PENDING_APPROVAL, UserStatus.REJECTED, UserStatus.SUSPENDED],
)
def test_non_active_users_cannot_use_a_session(status: UserStatus) -> None:
    assert (
        session_is_valid(
            expires_at=EXPIRES_AT,
            revoked_at=None,
            user_status=status,
            now=EXPIRES_AT - timedelta(minutes=1),
        )
        is False
    )


def test_the_stored_hash_is_sha256_hex() -> None:
    hashed = hash_session_token("raw-session-token")

    assert len(hashed) == 64
    assert set(hashed) <= set("0123456789abcdef")
    assert hashed == hash_session_token("raw-session-token")
    assert hashed != hash_session_token("another-token")
    assert "raw-session-token" not in hashed


def test_session_tokens_are_unique_and_url_safe() -> None:
    tokens = {generate_session_token() for _ in range(100)}

    assert len(tokens) == 100
    assert all(token.isascii() for token in tokens)
    assert all(
        all(character.isalnum() or character in "-_" for character in token) for token in tokens
    )
