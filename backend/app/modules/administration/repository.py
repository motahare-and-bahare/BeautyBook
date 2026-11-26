"""Persistence queries for the administrator user list.

Queries only read; they contain no authorization or pagination decisions. The page is fetched
with a keyset cursor, and roles are loaded for the whole page in one query so the list never
becomes an N+1 read path.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.modules.identity.models import User, UserRole


def list_users_page(
    session: Session,
    *,
    limit: int,
    after: tuple[datetime, uuid.UUID] | None,
) -> list[User]:
    """Return up to ``limit`` users ordered by ``created_at`` then ``id``, both descending.

    ``after`` is the sort key of the previous page's last row. The comparison is a strict
    "older than" keyset condition, so a row that was already returned can never appear again.
    """

    statement = select(User).order_by(User.created_at.desc(), User.id.desc()).limit(limit)

    if after is not None:
        moment, user_id = after
        statement = statement.where(
            or_(
                User.created_at < moment,
                and_(User.created_at == moment, User.id < user_id),
            )
        )

    return list(session.scalars(statement))


def roles_for_users(
    session: Session,
    user_ids: Sequence[uuid.UUID],
) -> dict[uuid.UUID, list[str]]:
    """Return the roles of every requested user in one query, sorted per user."""

    if not user_ids:
        return {}

    rows = session.execute(
        select(UserRole.user_id, UserRole.role)
        .where(UserRole.user_id.in_(user_ids))
        .order_by(UserRole.role)
    )

    roles: dict[uuid.UUID, list[str]] = {}
    for user_id, role in rows:
        roles.setdefault(user_id, []).append(role)
    return roles
