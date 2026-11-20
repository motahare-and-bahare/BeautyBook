"""Create the identity tables: users, user_roles, sessions, owner_applications.

Revision ID: 0001
Revises:
Create Date: 2026-11-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "status IN ('pending_approval', 'active', 'rejected', 'suspended')",
            name="ck_users_status",
        ),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_roles_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "role", name="pk_user_roles"),
        sa.CheckConstraint(
            "role IN ('customer', 'salon_owner', 'admin')",
            name="ck_user_roles_role",
        ),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_sessions_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    op.create_table(
        "owner_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("salon_name", sa.String(length=120), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_owner_applications_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name="fk_owner_applications_reviewed_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_owner_applications"),
        sa.UniqueConstraint("user_id", name="uq_owner_applications_user_id"),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_owner_applications_status",
        ),
        sa.CheckConstraint(
            "status <> 'rejected' OR rejection_reason IS NOT NULL",
            name="ck_owner_applications_rejection_reason",
        ),
        sa.CheckConstraint(
            "status = 'pending' OR reviewed_at IS NOT NULL",
            name="ck_owner_applications_reviewed_at",
        ),
    )
    op.create_index(
        "ix_owner_applications_status_submitted_at",
        "owner_applications",
        ["status", "submitted_at"],
    )


def downgrade() -> None:
    op.drop_table("owner_applications")
    op.drop_table("sessions")
    op.drop_table("user_roles")
    op.drop_table("users")
