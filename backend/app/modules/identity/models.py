"""SQLAlchemy 2.x mappings for accounts, roles, sessions, and owner applications.

Passwords are stored only as Argon2id hashes, and sessions store only a SHA-256 hash of the
opaque token. The database is the last line of defence: check constraints mirror the domain
values, and deleting an account removes its roles, sessions, and application.

There is no public administrator path in the data model. An ``admin`` row can only be created by
the administrative CLI or by an existing administrator, which later steps implement.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base
from app.modules.identity.domain import (
    APPLICATION_STATUS_VALUES,
    ROLE_VALUES,
    USER_STATUS_VALUES,
    OwnerApplicationStatus,
    UserStatus,
)


def _in_clause(column: str, values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(_in_clause("status", USER_STATUS_VALUES), name="ck_users_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserStatus.ACTIVE.value,
        server_default=UserStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    roles: Mapped[list[UserRole]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    owner_application: Mapped[OwnerApplication | None] = relationship(
        back_populates="user",
        foreign_keys="OwnerApplication.user_id",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviewed_applications: Mapped[list[OwnerApplication]] = relationship(
        back_populates="reviewer",
        foreign_keys="OwnerApplication.reviewed_by",
        passive_deletes=True,
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (CheckConstraint(_in_clause("role", ROLE_VALUES), name="ck_user_roles_role"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(String(20), primary_key=True)

    user: Mapped[User] = relationship(back_populates="roles")


class AuthSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_sessions_token_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="sessions")


class OwnerApplication(Base):
    __tablename__ = "owner_applications"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_owner_applications_user_id"),
        CheckConstraint(
            _in_clause("status", APPLICATION_STATUS_VALUES),
            name="ck_owner_applications_status",
        ),
        CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name="ck_owner_applications_rejection_reason",
        ),
        CheckConstraint(
            "status = 'pending' OR reviewed_at IS NOT NULL",
            name="ck_owner_applications_reviewed_at",
        ),
        Index(
            "ix_owner_applications_status_submitted_at",
            "status",
            "submitted_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    salon_name: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OwnerApplicationStatus.PENDING.value,
        server_default=OwnerApplicationStatus.PENDING.value,
    )
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(
        back_populates="owner_application",
        foreign_keys=[user_id],
    )
    reviewer: Mapped[User | None] = relationship(
        back_populates="reviewed_applications",
        foreign_keys=[reviewed_by],
    )
