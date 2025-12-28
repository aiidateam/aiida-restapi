"""Declaration of FastAPI router for users."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from fastapi import APIRouter, Depends, HTTPException, Query

from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.common.query import QueryParams
from aiida_restapi.repository.entity import EntityRepository

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/users')
write_router = APIRouter(prefix='/users')

repository = EntityRepository[orm.User, orm.User.Model](orm.User)


@read_router.get(
    '/schema',
    response_model=dict,
)
async def get_users_schema(
    which: t.Literal['get', 'post'] = Query(
        'get',
        description='Type of schema to retrieve: "get" or "post"',
    ),
) -> dict:
    """Get JSON schema for AiiDA users.

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


@read_router.get(
    '/projectable_properties',
    response_model=list[str],
)
async def get_user_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA user.

    :return: The list of projectable properties for AiiDA user.
    """
    return repository.get_projectable_properties()


@read_router.get(
    '',
    response_model=PaginatedResults[orm.User.Model],
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def get_users(
    query_params: t.Annotated[
        QueryParams,
        Query(
            default_factory=QueryParams,
            description='Query parameters for filtering, sorting, and pagination.',
        ),
    ],
) -> PaginatedResults[orm.User.Model]:
    """Get AiiDA users with optional filtering, sorting, and/or pagination.

    :param query_params: The query parameters, including filters, order_by, page_size, and page.
    :return: The paginated results, including total count, current page, page size, and list of user models.
    :raises HTTPException: 422 if the query parameters are invalid,
        500 for other failures during retrieval.
    """
    try:
        return repository.get_entities(query_params)
    except ValueError as exception:
        raise HTTPException(status_code=422, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@read_router.get(
    '/{pk}',
    response_model=orm.User.Model,
)
@with_dbenv()
async def get_user(pk: int) -> orm.User.Model:
    """Get AiiDA user by pk.

    :param pk: The pk of the user to retrieve.
    :return: The AiiDA user model.
    :raises HTTPException: 404 if the user with the given pk does not exist,
        500 for any other failures.
    """
    try:
        return repository.get_entity_by_id(pk)
    except NotExistent as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception


@write_router.post(
    '',
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
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))
