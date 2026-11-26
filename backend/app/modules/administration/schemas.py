"""Request and response schemas for administration endpoints.

The items reuse the identity module's ``UserResponse`` because it is already the canonical safe
view of an account: id, name, email, roles, status, and creation time, with no hash or token. A
second copy of those fields would drift from the authentication responses.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.modules.identity.schemas import UserResponse


class AdminUserListResponse(BaseModel):
    """One page of accounts plus the cursor for the next page, if any."""

    items: list[UserResponse]
    next_cursor: str | None = None
