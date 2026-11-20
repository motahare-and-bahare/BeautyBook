"""CSRF token generation and constant-time comparison."""

from __future__ import annotations

import secrets

import pytest

from app.core.security import CSRF_TOKEN_BYTES, generate_csrf_token, tokens_match


def test_generated_tokens_are_long_and_url_safe() -> None:
    token = generate_csrf_token()

    assert len(token) >= CSRF_TOKEN_BYTES
    assert token.isascii()
    assert all(character.isalnum() or character in "-_" for character in token)


def test_generated_tokens_do_not_repeat() -> None:
    tokens = {generate_csrf_token() for _ in range(200)}

    assert len(tokens) == 200


def test_identical_tokens_match() -> None:
    token = generate_csrf_token()

    assert tokens_match(token, token) is True


@pytest.mark.parametrize("provided", [None, "", "x"])
def test_missing_or_empty_tokens_never_match(provided: str | None) -> None:
    assert tokens_match("a" * 43, provided) is False


def test_a_truncated_or_extended_token_does_not_match() -> None:
    token = "a" * 43

    assert tokens_match(token, token[:-1]) is False
    assert tokens_match(token, token + "b") is False
    assert tokens_match(token, "b" * 43) is False
    assert tokens_match(token, token.upper()) is False


def test_non_ascii_input_does_not_raise() -> None:
    assert tokens_match("token", "توکن") is False


def test_comparison_uses_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[bytes, bytes]] = []
    real_compare_digest = secrets.compare_digest

    def spy(expected: bytes, provided: bytes) -> bool:
        calls.append((expected, provided))
        return real_compare_digest(expected, provided)

    monkeypatch.setattr("app.core.security.secrets.compare_digest", spy)

    assert tokens_match("expected-token", "expected-token") is True
    assert calls == [(b"expected-token", b"expected-token")]
