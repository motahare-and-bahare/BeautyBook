"""Administration use cases.

The administrator user list is a read-only projection: it returns accounts with their roles and
never exposes password hashes, session tokens, or owner-application details. Authorization is
enforced by the router's role dependency; this use case only applies the pagination rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.administration import repository
from app.modules.administration.domain import (
    DEFAULT_PAGE_LIMIT,
    decode_cursor,
    encode_cursor,
    ensure_limit_is_supported,
)
from app.modules.identity.models import User

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AdminUser:
    """One account with the roles read from the database."""

    user: User
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AdminUserPage:
    """One page of accounts and the cursor that continues the list."""

    items: tuple[AdminUser, ...]
    next_cursor: str | None


def list_users(
    session: Session,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    cursor: str | None = None,
) -> AdminUserPage:
    """Return one page of accounts, newest first.

    One extra row is fetched to learn whether another page exists without a second count query.
    The cursor is only issued when there really is more data, so a client can rely on
    ``next_cursor is None`` meaning "the end".
    """

    ensure_limit_is_supported(limit)
    after = decode_cursor(cursor) if cursor else None

    users = repository.list_users_page(session, limit=limit + 1, after=after)
    has_more = len(users) > limit
    visible = users[:limit]

    roles_by_user = repository.roles_for_users(session, [user.id for user in visible])
    items = tuple(
        AdminUser(user=user, roles=tuple(roles_by_user.get(user.id, []))) for user in visible
    )

    next_cursor = None
    if has_more and visible:
        last = visible[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    logger.info("admin_user_list_viewed count=%s has_more=%s", len(items), has_more)
    return AdminUserPage(items=items, next_cursor=next_cursor)
