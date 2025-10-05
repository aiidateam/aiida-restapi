"""Declaration of FastAPI application."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()


repository = EntityRepository[orm.User, orm.User.Model](orm.User)


@router.get('/users/projectable_properties', response_model=list[str])
async def get_user_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA user."""
    return repository.get_projectable_properties()


@router.get(
    '/users',
    response_model=PaginatedResults[orm.User.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_users(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.User.Model]:
    """Get AiiDA users with optional filtering, sorting, and/or pagination."""
    return repository.get_entities(queries)


@router.get(
    '/users/{user_id}',
    response_model=orm.User.Model,
)
@with_dbenv()
async def get_user(user_id: int) -> orm.User.Model:
    """Get AiiDA user by id."""
    return repository.get_entity_by_id(user_id)


@router.post(
    '/users',
    response_model=orm.User.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_user(
    user_model: orm.User.Model,
    current_user: t.Annotated[orm.User, Depends(get_current_active_user)],
) -> orm.User.Model:
    """Create new AiiDA user."""
    return repository.create_entity(user_model)
