"""Administration HTTP endpoints.

Every route in this module is administrator-only. The role check lives in the router's
dependencies, so a handler can never run for a caller without the ``admin`` role, and a missing
session is answered with ``401`` before ``403`` is considered. The UI is not trusted for this.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.infrastructure.database import get_session
from app.modules.administration import service
from app.modules.administration.domain import (
    CURSOR_MAX_LENGTH,
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
)
from app.modules.administration.schemas import AdminUserListResponse
from app.modules.identity.dependencies import CurrentUser, require_roles
from app.modules.identity.domain import DomainValidationError, Role
from app.modules.identity.schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])

DatabaseSession = Annotated[Session, Depends(get_session)]
Administrator = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    session: DatabaseSession,
    _administrator: Administrator,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    cursor: Annotated[str | None, Query(max_length=CURSOR_MAX_LENGTH)] = None,
) -> AdminUserListResponse:
    """List accounts newest first, with roles and pagination.

    ``limit`` is bounded and the cursor is opaque. A malformed cursor is a client error, so it is
    reported as ``422 INVALID_CURSOR`` instead of reaching the query.
    """

    try:
        page = service.list_users(session, limit=limit, cursor=cursor)
    except DomainValidationError as error:
        raise AppError(
            error.code,
            error.message,
            422,
            {error.field or "cursor": error.message},
        ) from error

    return AdminUserListResponse(
        items=[
            UserResponse(
                id=item.user.id,
                full_name=item.user.full_name,
                email=item.user.email,
                roles=list(item.roles),
                status=item.user.status,
                created_at=item.user.created_at,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )
