"""Declaration of FastAPI router for computers."""

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

read_router = APIRouter(prefix='/computers')
write_router = APIRouter(prefix='/computers')

service = EntityService[orm.Computer, orm.Computer.Model](orm.Computer)


@read_router.get(
    '/schema',
    response_model=dict,
)
async def get_computers_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA computers."""
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
async def get_computer_projections() -> list[str]:
    """Get queryable projections for AiiDA computers."""
    return service.get_projections()


@read_router.get(
    '',
    response_model=PaginatedResults[orm.Computer.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_computers(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Computer.Model]:
    """Get AiiDA computers with optional filtering, sorting, and/or pagination."""
    return service.get_many(queries)


@read_router.get(
    '/{pk}',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_computer(pk: str) -> orm.Computer.Model:
    """Get AiiDA computer by pk."""
    try:
        return service.get_one(pk)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{pk}/metadata',
    response_model=dict[str, t.Any],
)
@with_dbenv()
async def get_computer_metadata(pk: str) -> dict[str, t.Any]:
    """Get metadata of an AiiDA computer by pk."""
    try:
        return service.get_field(pk, 'metadata')
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_computer(
    computer_model: orm.Computer.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Computer.Model:
    """Create new AiiDA computer."""
    try:
        return service.add_one(computer_model)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))
