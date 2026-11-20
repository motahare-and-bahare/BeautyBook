"""Request and response schemas for identity endpoints.

Validation delegates to ``domain.py`` so the HTTP layer and the database use the same rules.
``extra="forbid"`` is the guard against mass assignment: a caller cannot send ``role``,
``status``, or ``is_active`` and have it silently ignored.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.identity.domain import (
    normalize_email,
    normalize_full_name,
    validate_password,
)


class RegisterCustomerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    email: str
    password: str

    @field_validator("full_name")
    @classmethod
    def _normalize_full_name(cls, value: str) -> str:
        return normalize_full_name(value)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password(value)


class LoginRequest(BaseModel):
    """Credentials for the login flow.

    The email is normalized exactly as during registration. The current password *policy* is not
    re-applied here: an existing password that predates a policy change must still be able to
    sign in, and a wrong short password simply fails verification. Only blank or absurdly long
    input is rejected as malformed.
    """

    model_config = ConfigDict(extra="forbid")

    email: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class UserResponse(BaseModel):
    """The safe public view of an account. Secrets never appear here."""

    id: uuid.UUID
    full_name: str
    email: str
    roles: list[str]
    status: str
    created_at: datetime
