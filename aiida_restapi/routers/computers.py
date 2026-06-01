"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Query

from aiida_restapi.common import errors, query
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.services.entity import EntityService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/computers')
write_router = APIRouter(prefix='/computers')

service = EntityService[orm.Computer, orm.Computer.Model](orm.Computer)


@read_router.get(
    '/schema',
    response_model=dict,
    responses={
        422: {'model': errors.RequestValidationError},
    },
)
async def get_computers_schema(
    which: t.Annotated[
        t.Literal['get', 'post'],
        Query(description='Type of schema to retrieve: "get" or "post"'),
    ] = 'get',
) -> dict:
    """Get JSON schema for AiiDA computers."""
    return service.get_schema(which=which)


@read_router.get(
    '/projections',
    response_model=list[str],
)
async def get_computer_projections() -> list[str]:
    """Get queryable projections for AiiDA computers."""
    return service.get_projections()


@read_router.get(
    '',
    response_model=PaginatedResults[orm.Computer.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_computers(
    query_params: t.Annotated[
        query.QueryParams,
        Depends(query.query_params),
    ],
) -> PaginatedResults[orm.Computer.Model]:
    """Get AiiDA computers with optional filtering, sorting, and/or pagination."""
    return service.get_many(query_params)


@read_router.get(
    '/{pk}',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': errors.RequestValidationError},
    },
)
@with_dbenv()
async def get_computer(pk: str) -> orm.Computer.Model:
    """Get AiiDA computer by pk."""
    return service.get_one(pk)


@read_router.get(
    '/{pk}/metadata',
    response_model=dict[str, t.Any],
    responses={
        404: {'model': errors.NonExistentError},
        409: {'model': errors.MultipleObjectsError},
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def get_computer_metadata(pk: str) -> dict[str, t.Any]:
    """Get metadata of an AiiDA computer by pk."""
    return service.get_field(pk, 'metadata')


@write_router.post(
    '',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        403: {'model': errors.StoringNotAllowedError},
        422: {'model': t.Union[errors.RequestValidationError, errors.InvalidInputError]},
    },
)
@with_dbenv()
async def create_computer(
    computer_model: orm.Computer.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Computer.Model:
    """Create new AiiDA computer."""
    return service.add_one(computer_model)
