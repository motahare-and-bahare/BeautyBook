"""First-administrator bootstrap: one active admin with the admin and customer roles.

The bootstrap command is the only path that creates an administrator without an existing
administrator. It must be atomic, must refuse a duplicate email, and must never store or log the
plain password. These tests run against the migrated test database.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.modules.identity import repository, service
from app.modules.identity.domain import DomainValidationError, UserStatus
from app.modules.identity.models import User, UserRole

ADMIN_EMAIL = "admin@beautybook.com"
ADMIN_PASSWORD = "bootstrap-password-1"


def count_rows(session: Session, model: type[User] | type[UserRole]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_creates_an_active_admin_with_admin_and_customer_roles(db_session: Session) -> None:
    result = service.create_admin(
        db_session,
        full_name="Site Administrator",
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )

    user = repository.get_user_by_email(db_session, ADMIN_EMAIL)
    assert user is not None
    assert user.id == result.user.id
    assert user.status == UserStatus.ACTIVE.value
    assert user.full_name == "Site Administrator"
    assert sorted(repository.list_roles(db_session, user.id)) == ["admin", "customer"]
    assert result.roles == ("admin", "customer")


def test_the_password_is_hashed_with_argon2id(db_session: Session) -> None:
    service.create_admin(
        db_session,
        full_name="Site Administrator",
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )

    user = repository.get_user_by_email(db_session, ADMIN_EMAIL)
    assert user is not None
    assert user.password_hash != ADMIN_PASSWORD
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(ADMIN_PASSWORD, user.password_hash) is True


def test_the_email_is_normalized(db_session: Session) -> None:
    service.create_admin(
        db_session,
        full_name="Site Administrator",
        email="  ADMIN@BeautyBook.COM ",
        password=ADMIN_PASSWORD,
    )

    assert repository.get_user_by_email(db_session, ADMIN_EMAIL) is not None


def test_a_duplicate_email_is_refused_without_changing_data(db_session: Session) -> None:
    service.create_admin(
        db_session,
        full_name="Site Administrator",
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )
    users_before = count_rows(db_session, User)
    roles_before = count_rows(db_session, UserRole)

    with pytest.raises(service.EmailAlreadyRegisteredError):
        service.create_admin(
            db_session,
            full_name="Someone Else",
            email=ADMIN_EMAIL.upper(),
            password="another-password-2",
        )

    db_session.expire_all()
    user = repository.get_user_by_email(db_session, ADMIN_EMAIL)
    assert user is not None
    assert user.full_name == "Site Administrator"
    assert count_rows(db_session, User) == users_before
    assert count_rows(db_session, UserRole) == roles_before


@pytest.mark.parametrize("password", ["short", " " * 20, "x" * 129])
def test_a_password_outside_the_policy_writes_nothing(db_session: Session, password: str) -> None:
    with pytest.raises(DomainValidationError):
        service.create_admin(
            db_session,
            full_name="Site Administrator",
            email=ADMIN_EMAIL,
            password=password,
        )

    assert repository.get_user_by_email(db_session, ADMIN_EMAIL) is None
    assert count_rows(db_session, User) == 0


def test_an_invalid_email_writes_nothing(db_session: Session) -> None:
    with pytest.raises(DomainValidationError):
        service.create_admin(
            db_session,
            full_name="Site Administrator",
            email="not-an-email",
            password=ADMIN_PASSWORD,
        )

    assert count_rows(db_session, User) == 0
