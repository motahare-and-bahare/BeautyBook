"""Administrator endpoints for the taxonomy and the user directory.

Two hard rules are enforced as dependencies, before the handler runs:

1. ``require_roles(Role.ADMIN)`` - authentication and role check. It runs first so a guest gets
   ``401`` rather than a confusing CSRF error.
2. ``require_csrf`` on writes - cookie-authenticated state changes need the double-submit token.

The backend stays authoritative: these checks do not replace per-endpoint tests, they are the
single place every admin route inherits.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.infrastructure.database import get_session
from app.modules.administration import service
from app.modules.administration.schemas import (
    AdminUserListResponse,
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.modules.identity.dependencies import (
    CurrentUser,
    require_csrf,
    require_roles,
)
from app.modules.identity.domain import Role

router = APIRouter(prefix="/admin", tags=["admin"])

DatabaseSession = Annotated[Session, Depends(get_session)]

CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"

_admin_only = require_roles(Role.ADMIN)


def _require_admin_and_csrf(
    admin: Annotated[CurrentUser, Depends(_admin_only)],
    _csrf: Annotated[None, Depends(require_csrf)],
) -> CurrentUser:
    """Authenticate, authorize, then verify CSRF - in that order."""

    return admin


AdminDep = Annotated[CurrentUser, Depends(_admin_only)]
AdminWriteDep = Annotated[CurrentUser, Depends(_require_admin_and_csrf)]


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    _admin: AdminDep,
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListResponse:
    """Read-only account directory. Secrets are never part of the projection."""

    page = service.list_users(session, limit=limit, offset=offset)
    return AdminUserListResponse(
        items=page.items,
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(_admin: AdminDep, session: DatabaseSession) -> list[CategoryResponse]:
    """Administrators see inactive categories too."""

    return [
        CategoryResponse.model_validate(category) for category in service.list_for_admin(session)
    ]


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    _admin: AdminWriteDep,
    session: DatabaseSession,
) -> CategoryResponse:
    try:
        category = service.create(
            session,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            is_active=payload.is_active,
            sort_order=payload.sort_order,
        )
    except service.CategoryConflictError as error:
        raise _conflict(error) from error
    return CategoryResponse.model_validate(category)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: uuid.UUID,
    _admin: AdminDep,
    session: DatabaseSession,
) -> CategoryResponse:
    try:
        category = service.get(session, category_id)
    except service.CategoryNotFoundError as error:
        raise _not_found() from error
    return CategoryResponse.model_validate(category)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    _admin: AdminWriteDep,
    session: DatabaseSession,
) -> CategoryResponse:
    try:
        category = service.update(
            session,
            category_id,
            changes=payload.model_dump(exclude_unset=True),
        )
    except service.CategoryNotFoundError as error:
        raise _not_found() from error
    except service.CategoryConflictError as error:
        raise _conflict(error) from error
    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    _admin: AdminWriteDep,
    session: DatabaseSession,
) -> Response:
    try:
        service.delete(session, category_id)
    except service.CategoryNotFoundError as error:
        raise _not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _not_found() -> AppError:
    return AppError(
        CATEGORY_NOT_FOUND,
        "The requested category does not exist.",
        404,
    )


def _conflict(error: service.CategoryConflictError) -> AppError:
    return AppError(error.code, error.message, 409)
