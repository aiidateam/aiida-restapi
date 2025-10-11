"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, HTTPException

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()


repository = EntityRepository[orm.Computer, orm.Computer.Model](orm.Computer)

ComputerPostModel = orm.Computer.InputModel


@router.get('/computers/schema')
async def get_computers_schema() -> dict[str, dict[str, t.Any]]:
    """Get JSON schema for AiiDA computers.

    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    """
    return {
        'get': orm.Computer.Model.model_json_schema(),
        'post': ComputerPostModel.model_json_schema(),
    }


@router.get('/computers/projectable_properties', response_model=list[str])
async def get_computer_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA computers.

    :return: The list of projectable properties for AiiDA computers.
    """
    return repository.get_projectable_properties()


@router.get(
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


@router.get(
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


@router.post(
    '/computers',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_computer(
    computer_model: orm.Computer.Model,
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Computer.Model:
    """Create new AiiDA computer.

    :param computer_model: The AiiDA ORM model of the computer to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA Computer model.
    """
    return repository.create_entity(computer_model)
