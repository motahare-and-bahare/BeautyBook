"""Persistence queries for identity tables.

Repositories only read and write rows; business decisions stay in the service and domain.
These functions flush so the caller can compose an atomic transaction but never commit.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.identity.domain import Role, UserStatus
from app.modules.identity.models import AuthSession, User, UserRole


def create_user(
    session: Session,
    *,
    full_name: str,
    email: str,
    password_hash: str,
    status: str = UserStatus.ACTIVE.value,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        status=status,
    )
    session.add(user)
    session.flush()
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def add_role(session: Session, *, user_id: uuid.UUID, role: Role) -> UserRole:
    user_role = UserRole(user_id=user_id, role=role.value)
    session.add(user_role)
    session.flush()
    return user_role


def list_roles(session: Session, user_id: uuid.UUID) -> list[str]:
    return list(
        session.scalars(
            select(UserRole.role).where(UserRole.user_id == user_id).order_by(UserRole.role)
        )
    )


def create_session(
    session: Session,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
) -> AuthSession:
    auth_session = AuthSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(auth_session)
    session.flush()
    return auth_session


def get_session_by_token_hash(session: Session, token_hash: str) -> AuthSession | None:
    return session.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash))


def get_user_by_id(session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def revoke_session(
    session: Session,
    auth_session: AuthSession,
    *,
    revoked_at: datetime,
) -> None:
    """Revoke once. Repeated calls keep the first revocation time."""

    if auth_session.revoked_at is None:
        auth_session.revoked_at = revoked_at
        session.flush()


def list_users_page(session: Session, *, limit: int, offset: int) -> Sequence[User]:
    """One administrator page, newest first with a stable tie-breaker."""

    return list(
        session.scalars(
            select(User).order_by(User.created_at.desc(), User.id).limit(limit).offset(offset)
        )
    )


def count_users(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(User)) or 0


def roles_by_user_id(
    session: Session,
    user_ids: Sequence[uuid.UUID],
) -> dict[uuid.UUID, list[str]]:
    """Batch role lookup so the directory stays at three queries, not one per user."""

    if not user_ids:
        return {}

    roles: dict[uuid.UUID, list[str]] = {}
    rows = session.execute(
        select(UserRole.user_id, UserRole.role)
        .where(UserRole.user_id.in_(user_ids))
        .order_by(UserRole.role)
    )
    for user_id, role in rows:
        roles.setdefault(user_id, []).append(role)
    return roles
