"""Declaration of FastAPI router for groups."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Query

from aiida_restapi.common import errors, query
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.services.entity import EntityService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/groups')
write_router = APIRouter(prefix='/groups')

service = EntityService[orm.Group, orm.Group.Model](orm.Group)


@read_router.get(
    '/schema',
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.RequestValidationError},
    },
)
async def get_groups_schema(
    which: t.Annotated[
        t.Literal['get', 'post'],
        Query(description='Type of schema to retrieve: "get" or "post"'),
    ] = 'get',
) -> dict[str, t.Any]:
    """Get JSON schema for AiiDA groups."""
    return service.get_schema(which=which)


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
    responses={
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_groups(
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[dict[str, t.Any]]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination."""
    return service.get_many(query_params)


@read_router.get(
    '/{uuid}',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_group(uuid: str) -> dict[str, t.Any]:
    """Get AiiDA group by uuid."""
    return service.get_one(uuid)


@read_router.get(
    '/{uuid}/user',
    response_model=orm.User.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_group_user(uuid: str) -> dict[str, t.Any]:
    """Get the user associated with a group."""
    return service.get_related_one(uuid, orm.User)


@read_router.get(
    '/{uuid}/nodes',
    response_model=PaginatedResults[orm.Node.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_group_nodes(
    uuid: str,
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[dict[str, t.Any]]:
    """Get the nodes of a group."""
    return service.get_related_many(uuid, orm.Node, query_params)


@read_router.get(
    '/{uuid}/extras',
    response_model=dict[str, t.Any],
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_group_extras(uuid: str) -> dict[str, t.Any]:
    """Get the extras of a group."""
    return service.get_field(uuid, 'extras')


@write_router.post(
    '',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        403: {'model': errors.StoringNotAllowedError},
        422: {'model': t.Union[errors.RequestValidationError, errors.InvalidInputError]},
    },
)
@with_dbenv()
async def create_group(
    group_model: orm.Group.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Create new AiiDA group."""
    return service.add_one(group_model)
