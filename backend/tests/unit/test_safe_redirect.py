"""Return paths are accepted only when they stay on this site."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import is_safe_redirect_path, safe_redirect_path


@pytest.mark.parametrize(
    "value",
    [
        "/account",
        "/owner",
        "/admin/owner-applications?status=pending",
        "/register/owner#salon",
        "/",
    ],
)
def test_accepts_local_absolute_paths(value: str) -> None:
    assert is_safe_redirect_path(value) is True


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "   ",
        " /account",
        "/account ",
        "account",
        "https://evil.example/account",
        "http://evil.example",
        "//evil.example",
        "/\\evil.example",
        "\\\\evil.example",
        "javascript:alert(1)",
        "/account\nSet-Cookie: stolen=1",
        "/account%0d%0aLocation:%20//evil.example",
    ],
)
def test_rejects_external_or_ambiguous_paths(value: str | None) -> None:
    assert is_safe_redirect_path(value) is False


def test_falls_back_to_the_default_for_an_unsafe_path() -> None:
    assert safe_redirect_path("//evil.example") == "/account"


def test_preserves_a_safe_path() -> None:
    assert safe_redirect_path("/owner?tab=services") == "/owner?tab=services"


def test_falls_back_to_a_custom_default() -> None:
    assert safe_redirect_path(None, default="/login") == "/login"
