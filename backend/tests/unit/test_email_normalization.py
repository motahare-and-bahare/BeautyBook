"""Email normalization is shared by every registration and login path."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import DomainValidationError, normalize_email


def test_trims_and_lowercases_the_address() -> None:
    assert normalize_email("  Customer@Example.COM \t") == "customer@example.com"


def test_allows_unicode_yet_normalizes_case() -> None:
    assert normalize_email("ÜSER@Example.com") == "üser@example.com"


def test_accepts_an_address_of_exactly_the_maximum_length() -> None:
    email = "a" * (254 - len("@example.com")) + "@example.com"

    assert len(email) == 254
    assert normalize_email(email) == email


def test_rejects_an_address_longer_than_the_maximum_length() -> None:
    email = "a" * (255 - len("@example.com")) + "@example.com"

    with pytest.raises(DomainValidationError) as error:
        normalize_email(email)

    assert error.value.code == "INVALID_EMAIL"
    assert error.value.field == "email"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "no-at-sign.example.com",
        "two@@example.com",
        "user@",
        "@example.com",
        "user@localhost",
        "user name@example.com",
        "user@exa mple.com",
        "user@example..com",
        "user@.com",
        "user@example.",
        ".user@example.com",
        "user\x00@example.com",
    ],
)
def test_rejects_malformed_addresses(value: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        normalize_email(value)

    assert error.value.code == "INVALID_EMAIL"
    assert error.value.field == "email"
