"""Model mappings and database constraints for identity tables."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.identity.domain import (
    ROLE_VALUES,
    OwnerApplicationStatus,
    UserStatus,
    normalize_email,
)
from app.modules.identity.models import AuthSession, OwnerApplication, User, UserRole

PASSWORD_HASH = "argon2id$v=19$m=65536,t=3,p=4$placeholder$placeholder"


def make_user(
    email: str = "user@example.com",
    status: str = UserStatus.ACTIVE.value,
) -> User:
    return User(full_name="Test User", email=email, password_hash=PASSWORD_HASH, status=status)


def make_session(user_id: uuid.UUID, token_hash: str | None = None) -> AuthSession:
    return AuthSession(
        user_id=user_id,
        token_hash=token_hash or "a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )


def make_application(user_id: uuid.UUID, **overrides: object) -> OwnerApplication:
    values: dict[str, object] = {
        "salon_name": "Studio Sample",
        "city": "Berlin",
        "phone": "+49 30 123456",
        "timezone": "Europe/Berlin",
        "currency": "EUR",
    }
    values.update(overrides)
    return OwnerApplication(user_id=user_id, **values)  # type: ignore[arg-type]


def test_users_receive_uuid_primary_keys(db_session: Session) -> None:
    user = make_user()

    db_session.add(user)
    db_session.commit()

    assert isinstance(user.id, uuid.UUID)


def test_sessions_and_owner_applications_receive_uuid_primary_keys(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    auth_session = make_session(user.id)
    application = make_application(user.id)
    db_session.add_all([auth_session, application])
    db_session.commit()

    assert isinstance(auth_session.id, uuid.UUID)
    assert isinstance(application.id, uuid.UUID)


def test_new_users_default_to_active(db_session: Session) -> None:
    user = User(full_name="Test User", email="default@example.com", password_hash=PASSWORD_HASH)

    db_session.add(user)
    db_session.commit()

    assert user.status == UserStatus.ACTIVE.value


def test_email_is_unique_after_normalization(db_session: Session) -> None:
    db_session.add(make_user(normalize_email("  Anna@Example.COM ")))
    db_session.commit()

    db_session.add(make_user(normalize_email("ANNA@example.com")))
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize("status", ["pending", "active ", "deleted", ""])
def test_users_reject_unknown_statuses(db_session: Session, status: str) -> None:
    db_session.add(make_user(status=status))

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_every_documented_role_is_accepted(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add_all([UserRole(user_id=user.id, role=role) for role in ROLE_VALUES])
    db_session.commit()

    stored = set(db_session.scalars(select(UserRole.role)).all())
    assert stored == set(ROLE_VALUES)


def test_roles_reject_unknown_values(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(UserRole(user_id=user.id, role="owner"))
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_a_role_cannot_be_granted_twice_to_the_same_user(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add_all(
        [
            UserRole(user_id=user.id, role="customer"),
            UserRole(user_id=user.id, role="customer"),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_session_token_hash_is_unique(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add_all([make_session(user.id), make_session(user.id)])
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_each_user_can_have_only_one_owner_application(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add_all([make_application(user.id), make_application(user.id)])
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_applications_reject_unknown_statuses(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(make_application(user.id, status="waiting"))
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_a_rejected_application_requires_a_reason(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(
        make_application(
            user.id,
            status=OwnerApplicationStatus.REJECTED.value,
            reviewed_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_a_reviewed_application_requires_a_review_timestamp(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    db_session.add(
        make_application(
            user.id,
            status=OwnerApplicationStatus.APPROVED.value,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_a_complete_rejection_is_accepted(db_session: Session) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()

    application = make_application(
        user.id,
        status=OwnerApplicationStatus.REJECTED.value,
        rejection_reason="Salon details could not be verified.",
        reviewed_at=datetime.now(UTC),
    )
    db_session.add(application)
    db_session.commit()

    assert application.status == OwnerApplicationStatus.REJECTED.value
    assert application.rejection_reason is not None


def test_deleting_a_user_cascades_to_roles_sessions_and_applications(
    db_session: Session,
) -> None:
    user = make_user()
    db_session.add(user)
    db_session.flush()
    db_session.add_all(
        [
            UserRole(user_id=user.id, role="customer"),
            make_session(user.id),
            make_application(user.id),
        ]
    )
    db_session.commit()

    db_session.delete(user)
    db_session.commit()

    for model in (UserRole, AuthSession, OwnerApplication):
        count = db_session.scalar(select(func.count()).select_from(model))
        assert count == 0


def test_deleting_the_reviewer_sets_the_reference_to_null(db_session: Session) -> None:
    applicant = make_user("applicant@example.com", UserStatus.PENDING_APPROVAL.value)
    reviewer = make_user("admin@example.com")
    db_session.add_all([applicant, reviewer])
    db_session.flush()

    application = make_application(
        applicant.id,
        status=OwnerApplicationStatus.APPROVED.value,
        reviewed_at=datetime.now(UTC),
        reviewed_by=reviewer.id,
    )
    db_session.add(application)
    db_session.commit()

    db_session.delete(reviewer)
    db_session.commit()
    db_session.refresh(application)

    assert application.reviewed_by is None
