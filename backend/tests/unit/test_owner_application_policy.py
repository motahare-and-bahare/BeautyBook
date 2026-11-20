"""Owner applications are reviewed once and rejections always carry a reason."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import (
    APPLICATION_STATUS_VALUES,
    REJECTION_REASON_MAX_LENGTH,
    DomainValidationError,
    OwnerApplicationStatus,
    can_transition_application_status,
    ensure_application_status_transition,
    validate_rejection_reason,
)


def test_status_values_match_the_database_constraint() -> None:
    assert APPLICATION_STATUS_VALUES == ("pending", "approved", "rejected")


@pytest.mark.parametrize(
    "target", [OwnerApplicationStatus.APPROVED, OwnerApplicationStatus.REJECTED]
)
def test_a_pending_application_can_be_reviewed(target: OwnerApplicationStatus) -> None:
    assert can_transition_application_status(OwnerApplicationStatus.PENDING, target) is True


@pytest.mark.parametrize(
    "current",
    [OwnerApplicationStatus.APPROVED, OwnerApplicationStatus.REJECTED],
)
def test_a_reviewed_application_cannot_be_reviewed_again(
    current: OwnerApplicationStatus,
) -> None:
    for target in OwnerApplicationStatus:
        assert can_transition_application_status(current, target) is False


def test_invalid_application_transition_raises_a_domain_error() -> None:
    with pytest.raises(DomainValidationError) as error:
        ensure_application_status_transition(
            OwnerApplicationStatus.APPROVED,
            OwnerApplicationStatus.REJECTED,
        )

    assert error.value.code == "INVALID_APPLICATION_TRANSITION"


def test_rejection_reason_is_trimmed() -> None:
    assert validate_rejection_reason("  incomplete salon details  ") == "incomplete salon details"


def test_rejection_reason_accepts_the_maximum_length() -> None:
    reason = "r" * REJECTION_REASON_MAX_LENGTH

    assert validate_rejection_reason(reason) == reason


@pytest.mark.parametrize("reason", [None, "", "   ", "\n\t"])
def test_rejection_requires_a_non_blank_reason(reason: str | None) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_rejection_reason(reason)

    assert error.value.code == "INVALID_REJECTION_REASON"
    assert error.value.field == "reason"


def test_rejection_reason_longer_than_the_maximum_is_rejected() -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_rejection_reason("r" * (REJECTION_REASON_MAX_LENGTH + 1))

    assert error.value.code == "INVALID_REJECTION_REASON"
