"""Roles are additive and only the customer role is assigned publicly."""

from __future__ import annotations

import pytest

from app.modules.identity.domain import (
    GRANTABLE_ROLES,
    PUBLIC_REGISTRATION_ROLES,
    ROLE_VALUES,
    DomainValidationError,
    Role,
    normalize_grantable_role,
)


def test_role_values_match_the_database_constraint() -> None:
    assert ROLE_VALUES == ("customer", "salon_owner", "admin")


def test_customer_is_the_only_publicly_assignable_role() -> None:
    assert frozenset({Role.CUSTOMER}) == PUBLIC_REGISTRATION_ROLES


def test_public_registration_can_never_grant_an_administrator() -> None:
    assert Role.ADMIN not in PUBLIC_REGISTRATION_ROLES


def test_public_registration_never_grants_the_owner_role() -> None:
    assert Role.SALON_OWNER not in PUBLIC_REGISTRATION_ROLES


def test_only_administrator_roles_can_be_granted_after_signup() -> None:
    assert frozenset({Role.ADMIN, Role.SALON_OWNER}) == GRANTABLE_ROLES


@pytest.mark.parametrize("role", ["admin", "salon_owner"])
def test_normalizes_a_grantable_role(role: str) -> None:
    assert normalize_grantable_role(role) is Role(role)


@pytest.mark.parametrize("role", ["customer", "administrator", "", "ADMIN"])
def test_rejects_non_grantable_roles(role: str) -> None:
    with pytest.raises(DomainValidationError) as error:
        normalize_grantable_role(role)

    assert error.value.code == "INVALID_ROLE"
    assert error.value.field == "role"
