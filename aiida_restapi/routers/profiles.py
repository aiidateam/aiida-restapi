"""Declaration of FastAPI router for profile discovery."""

from __future__ import annotations

from fastapi import APIRouter, Request

from aiida_restapi.models.profiles import ProfileList
from aiida_restapi.profiles import ProfileBackendRegistry

read_router = APIRouter(prefix='/profiles')


@read_router.get('', response_model=ProfileList)
async def get_profiles(request: Request) -> ProfileList:
    """List profile-scoped API profiles and identify the default."""
    registry: ProfileBackendRegistry = request.app.state.profile_backends
    return ProfileList(
        profiles=list(registry.profiles),
        default_profile=registry.default_profile,
    )
