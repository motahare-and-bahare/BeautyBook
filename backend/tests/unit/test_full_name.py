"""Full-name normalization: trimming, length, control characters, Unicode."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import DomainValidationError, normalize_full_name


def test_trims_surrounding_whitespace() -> None:
    assert normalize_full_name("  Sara Ahmadi  ") == "Sara Ahmadi"


def test_keeps_unicode_names() -> None:
    assert normalize_full_name("  سارا احمدی  ") == "سارا احمدی"
    assert normalize_full_name("Zoë Ångström") == "Zoë Ångström"


def test_accepts_the_minimum_and_maximum_length() -> None:
    assert normalize_full_name("Al") == "Al"
    assert normalize_full_name("a" * 100) == "a" * 100


@pytest.mark.parametrize("value", ["", "   ", "A", "a" * 101, "Sara\x00Ahmadi", "Sara\nAhmadi"])
def test_rejects_invalid_names(value: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        normalize_full_name(value)

    assert error.value.code == "INVALID_FULL_NAME"
    assert error.value.field == "full_name"
