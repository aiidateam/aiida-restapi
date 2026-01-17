"""Declaration of FastAPI router for groups."""

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

repository = EntityRepository[orm.Group, orm.Group.Model](orm.Group)


@read_router.get('/groups/schema')
async def get_groups_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA groups.

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


@read_router.get('/groups/projectable_properties', response_model=list[str])
async def get_group_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA groups.

    :return: The list of projectable properties for AiiDA groups.
    """
    return repository.get_projectable_properties()


@read_router.get(
    '/groups',
    response_model=PaginatedResults[orm.Group.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_groups(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Group.Model]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of group models.
    """
    return repository.get_entities(queries)


@read_router.get(
    '/groups/{uuid}',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_group(uuid: str) -> orm.Group.Model:
    """Get AiiDA group by uuid.

    :param uuid: The uuid of the group to retrieve.
    :return: The AiiDA group model.
    :raises HTTPException: 404 if a group with the given uuid does not exist,
        500 for any other server error.
    """
    try:
        return repository.get_entity_by_id(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/groups/{uuid}/extras',
    response_model=dict[str, t.Any],
)
@with_dbenv()
async def get_group_extras(uuid: str) -> dict[str, t.Any]:
    """Get the extras of a group.

    :param uuid: The uuid of the group to retrieve the extras for.
    :return: A dictionary with the group extras.
    :raises HTTPException: 404 if the group with the given uuid does not exist,
        500 for other failures during retrieval.
    """
    try:
        return repository.get_entity_extras(uuid)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '/groups',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_group(
    group_model: orm.Group.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Group.Model:
    """Create new AiiDA group.

    :param group_model: The Pydantic model of the group to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA Group model.
    :raises HTTPException: 500 for any failures during group creation.
    """
    try:
        return repository.create_entity(group_model)
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception
