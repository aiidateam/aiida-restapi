"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, HTTPException, Query

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import UserInDB, get_current_active_user

read_router = APIRouter()
write_router = APIRouter()


repository = EntityRepository[orm.Computer, orm.Computer.Model](orm.Computer)


@read_router.get('/computers/schema')
async def get_computers_schema(
    which: t.Literal['get', 'post'] | None = Query(
        None,
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA computers.

    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises HTTPException: If the 'which' parameter is not 'get' or 'post'.
    """
    if not which:
        return {
            'get': orm.Computer.Model.model_json_schema(),
            'post': orm.Computer.CreateModel.model_json_schema(),
        }
    elif which == 'get':
        return orm.Computer.Model.model_json_schema()
    elif which == 'post':
        return orm.Computer.CreateModel.model_json_schema()
    raise HTTPException(status_code=400, detail='Parameter "which" must be either "get" or "post"')


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
    '/computers/{comp_id}',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_computer(comp_id: int) -> orm.Computer.Model:
    """Get AiiDA computer by id.

    :param comp_id: The id of the AiiDA computer.
    :return: The computer model.
    :raises HTTPException: If the computer with the given id does not exist (404).
    """
    try:
        return repository.get_entity_by_id(comp_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f'Could not find any Computer with id {comp_id}')


@write_router.post(
    '/computers',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
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
    """
    return repository.create_entity(computer_model)
