"""Declaration of FastAPI router for groups."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Query, Request

from aiida_restapi.common import query
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.aiida import (
    GroupCollectionDocument,
    GroupResourceDocument,
    NodeCollectionDocument,
    UserResourceDocument,
)
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.jsonapi.responses import JsonApiResponse
from aiida_restapi.services.entity import EntityService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/groups')
write_router = APIRouter(prefix='/groups')

service = EntityService[orm.Group, orm.Group.Model](orm.Group)


@read_router.get(
    '/schema',
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
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
    response_class=JsonApiResponse,
    response_model=GroupCollectionDocument,
    response_model_exclude_none=True,
    responses={
        422: {
            'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError],
            'description': 'Validation Error | Query Builder Error',
        },
    },
)
@with_dbenv()
async def get_groups(
    request: Request,
    query_params: t.Annotated[
        query.CollectionQueryParams,
        Depends(query.collection_query_params),
    ],
) -> dict[str, t.Any]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination."""
    results = service.get_many(query_params)
    return JsonApi.collection(
        request,
        results,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
        query_params=query_params,
    )


@read_router.get(
    '/{uuid}',
    response_class=JsonApiResponse,
    response_model=GroupResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
@with_dbenv()
async def get_group(
    request: Request,
    uuid: str,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get AiiDA group by uuid."""
    result = service.get_one(uuid)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
        include=query_params.include,
    )


@read_router.get(
    '/{uuid}/user',
    response_class=JsonApiResponse,
    response_model=UserResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
@with_dbenv()
async def get_group_user(request: Request, uuid: str) -> dict[str, t.Any]:
    """Get the user associated with a group."""
    user = service.get_related_one(uuid, orm.User)
    return JsonApi.resource(
        request,
        user,
        resource_identity=orm.User.identity_field,
        resource_type='users',
    )


@read_router.get(
    '/{uuid}/nodes',
    response_class=JsonApiResponse,
    response_model=NodeCollectionDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {
            'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError],
            'description': 'Validation Error | Query Builder Error',
        },
    },
)
@with_dbenv()
async def get_group_nodes(
    request: Request,
    uuid: str,
    query_params: t.Annotated[
        query.CollectionQueryParams,
        Depends(query.collection_query_params),
    ],
) -> dict[str, t.Any]:
    """Get the nodes of a group."""
    nodes = service.get_related_many(uuid, orm.Node, query_params)
    return JsonApi.collection(
        request,
        nodes,
        resource_identity=orm.Node.identity_field,
        resource_type='nodes',
        query_params=query_params,
    )


@read_router.get(
    '/{uuid}/extras',
    response_class=JsonApiResponse,
    response_model=JsonApiResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {
            'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError],
            'description': 'Validation Error | Query Builder Error',
        },
    },
)
@with_dbenv()
async def get_group_extras(
    request: Request,
    uuid: str,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get the extras of a group."""
    extras = service.get_field(uuid, 'extras')
    return JsonApi.child_resource(
        request,
        extras,
        pid=uuid,
        parent_type='groups',
        child_type='extras',
        include=query_params.include,
    )


@write_router.post(
    '',
    response_class=JsonApiResponse,
    response_model=GroupResourceDocument,
    response_model_exclude_none=True,
    responses={
        403: {'model': errors.StoringNotAllowedError, 'description': 'Storing Not Allowed'},
        422: {
            'model': t.Union[errors.RequestValidationError, errors.InvalidInputError],
            'description': 'Validation Error | Invalid Input Error',
        },
    },
)
@with_dbenv()
async def create_group(
    request: Request,
    group_model: orm.Group.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Create new AiiDA group."""
    result = service.add_one(group_model)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
    )
