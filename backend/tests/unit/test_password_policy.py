"""Password policy: length only, no composition rules."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    DomainValidationError,
    validate_password,
)


def test_policy_bounds_are_documented_constants() -> None:
    assert PASSWORD_MIN_LENGTH == 12
    assert PASSWORD_MAX_LENGTH == 128


def test_accepts_the_minimum_length() -> None:
    password = "a" * 12

    assert validate_password(password) == password


def test_accepts_the_maximum_length() -> None:
    password = "a" * 128

    assert validate_password(password) == password


def test_rejects_one_character_short_of_the_minimum() -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_password("a" * 11)

    assert error.value.code == "INVALID_PASSWORD"
    assert error.value.field == "password"


def test_rejects_one_character_over_the_maximum() -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_password("a" * 129)

    assert error.value.code == "INVALID_PASSWORD"
    assert error.value.field == "password"


@pytest.mark.parametrize("password", ["", "          ", " " * 12, "\t\n" * 6])
def test_rejects_whitespace_only_passwords(password: str) -> None:
    with pytest.raises(DomainValidationError):
        validate_password(password)


def test_imposes_no_composition_rules() -> None:
    password = "all lowercase letters"

    assert validate_password(password) == password


def test_allows_unicode_and_preserves_the_value() -> None:
    password = "رمز عبور بسیار طولانی ۱۲۳"

    assert validate_password(password) == password


def test_does_not_trim_the_password() -> None:
    password = "  padded password  "

    assert validate_password(password) == password
