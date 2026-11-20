"""Argon2id password hashing and verification."""

from __future__ import annotations

import pytest
from argon2 import PasswordHasher

from app.core.config import get_settings
from app.core.security import hash_password, password_needs_rehash, verify_password

PASSWORD = "correct horse battery staple"


def test_hash_is_argon2id_and_does_not_contain_the_plaintext() -> None:
    hashed = hash_password(PASSWORD)

    assert hashed.startswith("$argon2id$")
    assert PASSWORD not in hashed
    assert len(hashed) <= 255


def test_the_same_password_gets_a_different_salt_each_time() -> None:
    first = hash_password(PASSWORD)
    second = hash_password(PASSWORD)

    assert first != second


def test_hashing_uses_the_configured_cost_parameters() -> None:
    settings = get_settings()

    hashed = hash_password(PASSWORD)

    assert f"m={settings.argon2_memory_cost}" in hashed
    assert f"t={settings.argon2_time_cost}" in hashed
    assert f"p={settings.argon2_parallelism}" in hashed


def test_a_correct_password_is_verified() -> None:
    hashed = hash_password(PASSWORD)

    assert verify_password(PASSWORD, hashed) is True


def test_a_wrong_password_is_rejected() -> None:
    hashed = hash_password(PASSWORD)

    assert verify_password("this is not the right password", hashed) is False


def test_an_unusable_hash_is_rejected_instead_of_raising() -> None:
    assert verify_password(PASSWORD, "not-a-valid-argon2-hash") is False


def test_a_current_hash_does_not_need_a_rehash() -> None:
    assert password_needs_rehash(hash_password(PASSWORD)) is False


def test_a_weaker_hash_needs_a_rehash(monkeypatch: pytest.MonkeyPatch) -> None:
    weak_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    monkeypatch.setattr(get_settings(), "argon2_time_cost", 2)

    assert password_needs_rehash(weak_hash) is True
