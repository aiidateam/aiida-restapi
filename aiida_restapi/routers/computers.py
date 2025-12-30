"""Declaration of FastAPI router for computers."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, Query, Request

from aiida_restapi.common import query
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.aiida import ComputerCollectionDocument, ComputerResourceDocument
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.jsonapi.responses import JsonApiResponse
from aiida_restapi.services.entity import EntityService

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/computers')
write_router = APIRouter(prefix='/computers')

service = EntityService[orm.Computer, orm.Computer.Model](orm.Computer)


@read_router.get(
    '/schema',
    response_model=dict[str, t.Any],
    responses={
        422: {'model': errors.RequestValidationError, 'description': 'Validation Error'},
    },
)
async def get_computers_schema(
    which: t.Annotated[
        t.Literal['get', 'post'],
        Query(description='Type of schema to retrieve: "get" or "post"'),
    ] = 'get',
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
    '/{pk}',
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
    pk: int,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get AiiDA computer by pk."""
    result = service.get_one(pk)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Computer.identity_field,
        resource_type='computers',
        include=query_params.include,
    )


@read_router.get(
    '/{pk}/metadata',
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
    pk: str,
    query_params: t.Annotated[
        query.ResourceQueryParams,
        Depends(query.resource_query_params),
    ],
) -> dict[str, t.Any]:
    """Get metadata of an AiiDA computer by pk."""
    metadata = service.get_field(pk, 'metadata')
    return JsonApi.child_resource(
        request,
        metadata,
        pid=str(pk),
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
    computer_model: orm.Computer.CreateModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Create new AiiDA computer."""
    result = service.add_one(computer_model)
    return JsonApi.resource(
        request,
        result,
        resource_identity=orm.Computer.identity_field,
        resource_type='computers',
    )
