"""Declaration of FastAPI router for groups."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from fastapi import APIRouter, Depends, HTTPException, Query

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams, query_params
from aiida_restapi.services.entity import EntityService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/groups')
write_router = APIRouter(prefix='/groups')

service = EntityService[orm.Group, orm.Group.Model](orm.Group)


@read_router.get(
    '/schema',
    response_model=dict,
)
async def get_groups_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA groups."""
    try:
        return service.get_schema(which=which)
    except ValueError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/projections',
    response_model=list[str],
)
async def get_group_projections() -> list[str]:
    """Get queryable projections for AiiDA groups."""
    return service.get_projections()


@read_router.get(
    '',
    response_model=PaginatedResults[orm.Group.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_groups(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Group.Model]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination."""
    return service.get_many(queries)


@read_router.get(
    '/{uuid}',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_group(uuid: str) -> orm.Group.Model:
    """Get AiiDA group by uuid."""
    try:
        return service.get_one(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{uuid}/extras',
    response_model=dict[str, t.Any],
)
@with_dbenv()
async def get_group_extras(uuid: str) -> dict[str, t.Any]:
    """Get the extras of a group."""
    try:
        return service.get_field(uuid, 'extras')
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_group(
    group_model: orm.Group.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Group.Model:
    """Create new AiiDA group."""
    try:
        return service.add_one(group_model)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception
