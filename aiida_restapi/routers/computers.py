"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Query, Request

from aiida_restapi import query
from aiida_restapi.common.responses import JsonApiResponse, JsonSchemaResponse
from aiida_restapi.common.types import EntityIdentifier
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.aiida import ComputerCollectionDocument, ComputerResourceDocument
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.services.entity import EntityService

read_router = APIRouter(prefix='/computers')
write_router = APIRouter(prefix='/computers')

service = EntityService[orm.Computer, orm.Computer.ReadModel](orm.Computer)


@read_router.get(
    '/schema',
    response_class=JsonSchemaResponse,
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
async def get_computers_schema(
    which: t.Annotated[
        t.Literal['read', 'write'],
        Query(description='Type of schema to retrieve: "read" or "write"'),
    ] = 'read',
) -> dict[str, t.Any]:
    """Get JSON schema for AiiDA computers."""
    return service.get_schema(which=which)


@read_router.get(
    '/projections',
    response_model=list[str],
)
async def get_computer_projections() -> list[str]:
    """Get queryable projections for AiiDA computers."""
    return service.get_projections()


@read_router.get(
    '',
    response_model=ComputerCollectionDocument,
    response_class=JsonApiResponse,
    response_model_exclude_none=True,
    responses={
        422: {
            'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError],
            'description': 'Validation Error | Query Builder Error',
        },
    },
)
@with_dbenv()
async def get_computers(
    request: Request,
    query_params: t.Annotated[
        query.CollectionQueryParams,
        Depends(query.collection_query_params),
    ],
) -> dict[str, t.Any]:
    """Get AiiDA computers with optional filtering, sorting, and/or pagination."""
    results = service.get_many(query_params)
    return JsonApi.collection(
        request,
        results,
        resource_identity=orm.Computer.identity_field,
        resource_type='computers',
        query_params=query_params,
    )


@read_router.get(
    '/{identifier}',
    response_class=JsonApiResponse,
    response_model=ComputerResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError, 'description': 'Resource Not Found'},
        409: {'model': errors.MultipleObjectsError, 'description': 'Multiple Resources Found'},
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
@with_dbenv()
async def get_computer(
    request: Request,
    identifier: EntityIdentifier,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get AiiDA computer."""
    result = service.get_one(identifier)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Computer.identity_field,
        resource_type='computers',
        include=query_params.include,
    )


@read_router.get(
    '/{identifier}/metadata',
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
async def get_computer_metadata(
    request: Request,
    identifier: EntityIdentifier,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get metadata of an AiiDA computer."""
    computer = service.load_one(identifier)
    metadata = service.get_field(identifier, 'metadata')
    return JsonApi.child_resource(
        request,
        metadata,
        pid=computer.uuid,
        parent_type='computers',
        child_type='metadata',
        include=query_params.include,
    )


@write_router.post(
    '',
    response_class=JsonApiResponse,
    response_model=ComputerResourceDocument,
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
async def create_computer(
    request: Request,
    computer_model: orm.Computer.WriteModel,
) -> dict[str, t.Any]:
    """Create new AiiDA computer."""
    result = service.add(computer_model)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Computer.identity_field,
        resource_type='computers',
    )
