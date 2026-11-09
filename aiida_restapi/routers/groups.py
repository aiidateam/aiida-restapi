"""Declaration of FastAPI router for groups."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.orm.implementation import StorageBackend
from fastapi import APIRouter, Depends, Query, Request

from aiida_restapi.common import query
from aiida_restapi.common.responses import JsonApiResponse, JsonSchemaResponse
from aiida_restapi.common.types import EntityIdentifier
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.aiida import (
    GroupCollectionDocument,
    GroupResourceDocument,
    NodeCollectionDocument,
    UserResourceDocument,
)
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.profiles import get_profile_backend
from aiida_restapi.services.entity import EntityService

metadata_router = APIRouter()
read_router = APIRouter(prefix='/groups')
write_router = APIRouter(prefix='/groups')

service = EntityService[orm.Group, orm.Group.ReadModel](orm.Group)


@metadata_router.get(
    '/schemas/groups',
    response_class=JsonSchemaResponse,
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
async def get_groups_schema(
    which: t.Annotated[
        t.Literal['read', 'write'],
        Query(description='Type of schema to retrieve: "read" or "write"'),
    ] = 'read',
) -> dict[str, t.Any]:
    """Get JSON schema for AiiDA groups."""
    return service.get_schema(which=which)


@metadata_router.get(
    '/projections/groups',
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
async def get_groups(
    request: Request,
    query_params: t.Annotated[
        query.CollectionQueryParams,
        Depends(query.collection_query_params),
    ],
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Get AiiDA groups with optional filtering, sorting, and/or pagination."""
    results = service.get_many(query_params, backend)
    return JsonApi.collection(
        request,
        results,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
        query_params=query_params,
        backend=backend,
    )


@read_router.get(
    '/{identifier}',
    response_class=JsonApiResponse,
    response_model=GroupResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
async def get_group(
    request: Request,
    identifier: EntityIdentifier,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Get AiiDA group."""
    result = service.get_one(identifier, backend)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
        include=query_params.include,
        backend=backend,
    )


@read_router.get(
    '/{identifier}/user',
    response_class=JsonApiResponse,
    response_model=UserResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
async def get_group_user(
    request: Request,
    identifier: EntityIdentifier,
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Get the user associated with a group."""
    user = service.get_related_one(identifier, orm.User, backend)
    return JsonApi.resource(
        request,
        user,
        resource_identity=orm.User.identity_field,
        resource_type='users',
        backend=backend,
    )


@read_router.get(
    '/{identifier}/nodes',
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
async def get_group_nodes(
    request: Request,
    identifier: EntityIdentifier,
    query_params: t.Annotated[
        query.CollectionQueryParams,
        Depends(query.collection_query_params),
    ],
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Get the nodes of a group."""
    nodes = service.get_related_many(identifier, orm.Node, query_params, backend)
    return JsonApi.collection(
        request,
        nodes,
        resource_identity=orm.Node.identity_field,
        resource_type='nodes',
        query_params=query_params,
        backend=backend,
    )


@read_router.get(
    '/{identifier}/extras',
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
async def get_group_extras(
    request: Request,
    identifier: EntityIdentifier,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Get the extras of a group."""
    group = service.load_one(identifier, backend)
    extras = service.get_field(identifier, 'extras', backend)
    return JsonApi.child_resource(
        request,
        extras,
        pid=group.uuid,
        parent_type='groups',
        child_type='extras',
        include=query_params.include,
        backend=backend,
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
async def create_group(
    request: Request,
    group_model: orm.Group.WriteModel,
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Create new AiiDA group."""
    result = service.add(group_model, backend)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Group.identity_field,
        resource_type='groups',
        backend=backend,
    )
