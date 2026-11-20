"""Salon locale values: IANA timezones and ISO 4217 currencies."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import (
    DomainValidationError,
    validate_currency,
    validate_timezone,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Europe/Berlin", "Europe/Berlin"),
        ("  Asia/Tehran  ", "Asia/Tehran"),
        ("UTC", "UTC"),
        ("America/Argentina/Buenos_Aires", "America/Argentina/Buenos_Aires"),
    ],
)
def test_accepts_iana_timezones(value: str, expected: str) -> None:
    assert validate_timezone(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", "   ", "Mars/Olympus", "europe/berlin", "../etc/passwd", "/etc/passwd", "UTC+3"],
)
def test_rejects_unknown_or_unsafe_timezones(value: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_timezone(value)

    assert error.value.code == "INVALID_TIMEZONE"
    assert error.value.field == "timezone"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("USD", "USD"), (" eur ", "EUR"), ("irr", "IRR")],
)
def test_accepts_iso_4217_currencies_and_normalizes_case(value: str, expected: str) -> None:
    assert validate_currency(value) == expected


@pytest.mark.parametrize("value", ["", "US", "US$", "XYZ", "EURO", "12A"])
def test_rejects_unknown_currencies(value: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        validate_currency(value)

    assert error.value.code == "INVALID_CURRENCY"
    assert error.value.field == "currency"
