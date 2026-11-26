"""Composition of the ``/api/v1`` routers.

Feature routers are added here as they are implemented. The health endpoints are mounted at
the application root instead, because orchestrators expect them outside the versioned API.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.administration.router import router as administration_router
from app.modules.identity.router import router as identity_router

router = APIRouter()
router.include_router(identity_router)
router.include_router(administration_router)
