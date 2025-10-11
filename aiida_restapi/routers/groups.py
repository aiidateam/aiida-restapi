"""Declaration of FastAPI router for groups."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, HTTPException

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()

repository = EntityRepository[orm.Group, orm.Group.Model](orm.Group)

GroupPostModel = orm.Group.InputModel


@router.get('/groups/schema')
async def get_groups_schema() -> dict[str, dict[str, t.Any]]:
    """Get JSON schema for AiiDA groups.

    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    """
    return {
        'get': orm.Group.Model.model_json_schema(),
        'post': GroupPostModel.model_json_schema(),
    }


@router.get('/groups/projectable_properties', response_model=list[str])
async def get_group_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA groups.

    :return: The list of projectable properties for AiiDA groups.
    """
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
    """Get AiiDA groups with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of group models.
    """
    return repository.get_entities(queries)


@router.get(
    '/groups/{group_id}',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_group(group_id: int) -> orm.Group.Model:
    """Get AiiDA group by id.

    :param group_id: The id of the group to retrieve.
    :return: The AiiDA group model.
    :raises HTTPException: If the group with the given id does not exist (404).
    """
    try:
        return repository.get_entity_by_id(group_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f'Could not find any Group with id {group_id}')


@router.post(
    '/groups',
    response_model=orm.Group.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_group(
    group_model: GroupPostModel,  # type: ignore[valid-type]
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Group.Model:
    """Create new AiiDA group.

    :param group_model: The Pydantic model of the group to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA Group model.
    """
    return repository.create_entity(group_model)
