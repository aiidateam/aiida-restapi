"""Declaration of FastAPI application."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()

repository = EntityRepository[orm.Group, orm.Group.Model](orm.Group)


@router.get('/groups/projectable_properties', response_model=list[str])
async def get_group_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA groups."""
    return repository.get_projectable_properties()


@router.get(
    '/groups',
    response_model=PaginatedResults[orm.Group.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_groups(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Group.Model]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination."""
    return repository.get_entities(queries)


@router.get(
    '/groups/{group_id}',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_group(group_id: int) -> orm.Group.Model:
    """Get AiiDA group by id."""
    return repository.get_entity_by_id(group_id)


@router.post(
    '/groups',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_group(
    group_model: orm.Group.Model,
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Group.Model:
    """Create new AiiDA group."""
    return repository.create_entity(group_model)
