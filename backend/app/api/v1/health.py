"""Liveness and readiness checks.

``/health`` proves the process is alive and never touches the database. ``/ready`` checks
that the database answers a trivial query.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.infrastructure.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(session: DatabaseSession) -> dict[str, str]:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("database readiness check failed")
        raise AppError(
            "DATABASE_UNAVAILABLE",
            "The database is not available.",
            503,
        ) from exc
    return {"status": "ready", "database": "ok"}
