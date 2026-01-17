"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from fastapi import APIRouter, Depends, HTTPException, Query

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams, query_params
from aiida_restapi.repository.entity import EntityRepository

from .auth import UserInDB, get_current_active_user

read_router = APIRouter()
write_router = APIRouter()

repository = EntityRepository[orm.Computer, orm.Computer.Model](orm.Computer)


@read_router.get('/computers/schema')
async def get_computers_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA computers.

    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises HTTPException: 422 if the 'which' parameter is not 'get' or 'post',
        500 for any other failures.
    """
    try:
        return repository.get_entity_schema(which=which)
    except ValueError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get('/computers/projectable_properties', response_model=list[str])
async def get_computer_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA computers.

    :return: The list of projectable properties for AiiDA computers.
    """
    return repository.get_projectable_properties()


@read_router.get(
    '/computers',
    response_model=PaginatedResults[orm.Computer.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_computers(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Computer.Model]:
    """Get AiiDA computers with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of computer models.
    """
    return repository.get_entities(queries)


@read_router.get(
    '/computers/{pk}',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_computer(pk: str) -> orm.Computer.Model:
    """Get AiiDA computer by pk.

    :param pk: The pk of the AiiDA computer.
    :return: The computer model.
    :raises HTTPException: 404 if the computer with the given pk does not exist,
        500 for any other failures.
    """
    try:
        return repository.get_entity_by_id(pk)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get('/computers/{pk}/metadata', response_model=dict[str, t.Any])
@with_dbenv()
async def get_computer_metadata(pk: str) -> dict[str, t.Any]:
    """Get metadata of an AiiDA computer by pk.

    :param pk: The pk of the AiiDA computer.
    :return: The metadata dictionary of the computer.
    :raises HTTPException: 404 if the computer with the given pk does not exist,
        500 for any other failures.
    """
    try:
        computer = repository.get_entity_by_id(pk)
        return computer.metadata
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '/computers',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_computer(
    computer_model: orm.Computer.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Computer.Model:
    """Create new AiiDA computer.

    :param computer_model: The AiiDA ORM model of the computer to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA Computer model.
    :raises HTTPException: 500 for any failures during computer creation.
    """
    try:
        return repository.create_entity(computer_model)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))
