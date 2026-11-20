"""User account statuses and the transitions the server may perform."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import (
    USER_STATUS_VALUES,
    DomainValidationError,
    UserStatus,
    can_authenticate,
    can_transition_user_status,
    ensure_user_status_transition,
)


def test_status_values_match_the_database_constraint() -> None:
    assert USER_STATUS_VALUES == ("pending_approval", "active", "rejected", "suspended")


@pytest.mark.parametrize(
    ("status", "allowed"),
    [
        (UserStatus.PENDING_APPROVAL, False),
        (UserStatus.ACTIVE, True),
        (UserStatus.REJECTED, False),
        (UserStatus.SUSPENDED, False),
    ],
)
def test_only_active_accounts_may_authenticate(status: UserStatus, allowed: bool) -> None:
    assert can_authenticate(status) is allowed


@pytest.mark.parametrize("target", [UserStatus.ACTIVE, UserStatus.REJECTED])
def test_a_pending_application_can_be_approved_or_rejected(target: UserStatus) -> None:
    assert can_transition_user_status(UserStatus.PENDING_APPROVAL, target) is True


def test_a_pending_account_cannot_be_suspended_directly() -> None:
    assert can_transition_user_status(UserStatus.PENDING_APPROVAL, UserStatus.SUSPENDED) is False


def test_an_active_account_can_be_suspended_and_restored() -> None:
    assert can_transition_user_status(UserStatus.ACTIVE, UserStatus.SUSPENDED) is True
    assert can_transition_user_status(UserStatus.SUSPENDED, UserStatus.ACTIVE) is True


def test_a_rejected_account_has_no_transition() -> None:
    assert can_transition_user_status(UserStatus.REJECTED, UserStatus.ACTIVE) is False
    assert can_transition_user_status(UserStatus.REJECTED, UserStatus.PENDING_APPROVAL) is False


def test_a_status_cannot_transition_to_itself() -> None:
    for status in UserStatus:
        assert can_transition_user_status(status, status) is False


def test_invalid_transition_raises_a_domain_error() -> None:
    with pytest.raises(DomainValidationError) as error:
        ensure_user_status_transition(UserStatus.REJECTED, UserStatus.ACTIVE)

    assert error.value.code == "INVALID_STATUS_TRANSITION"


def test_valid_transition_returns_none() -> None:
    assert ensure_user_status_transition(UserStatus.PENDING_APPROVAL, UserStatus.ACTIVE) is None
