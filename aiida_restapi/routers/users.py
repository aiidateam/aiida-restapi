"""Declaration of FastAPI router for users."""

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

router = APIRouter()

repository = EntityRepository[orm.User, orm.User.Model](orm.User)


@router.get('/users/schema')
async def get_users_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA users.

    :param which: The type of schema to retrieve: 'get' or 'post'.
    :return: A dictionary with 'get' and 'post' keys containing the respective JSON schemas.
    :raises HTTPException: 422 if the 'which' parameter is not 'get' or 'post'.
    """
    try:
        return repository.get_entity_schema(which=which)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


@router.get('/users/projectable_properties', response_model=list[str])
async def get_user_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA user.

    :return: The list of projectable properties for AiiDA user.
    """
    return repository.get_projectable_properties()


@router.get(
    '/users',
    response_model=PaginatedResults[orm.User.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_users(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.User.Model]:
    """Get AiiDA users with optional filtering, sorting, and/or pagination.

    :param queries: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of user models.
    """
    return repository.get_entities(queries)


@router.get(
    '/users/{user_id}',
    response_model=orm.User.Model,
)
@with_dbenv()
async def get_user(user_id: int) -> orm.User.Model:
    """Get AiiDA user by id.

    :param user_id: The id of the user to retrieve.
    :return: The AiiDA user model.
    :raises HTTPException: 404 if the user with the given id does not exist,
    """
    try:
        return repository.get_entity_by_id(user_id)
    except NotExistent:
        raise HTTPException(status_code=404, detail=f'Could not find a User with id {user_id}')


@router.post(
    '/users',
    response_model=orm.User.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def create_user(
    user_model: orm.User.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.User.Model:
    """Create new AiiDA user.

    :param user_model: The Pydantic model of the user to create.
    :param current_user: The current authenticated user.
    :return: The created AiiDA User model.
    :raises HTTPException: 500 for any failures during user creation.
    """
    try:
        return repository.create_entity(user_model)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
