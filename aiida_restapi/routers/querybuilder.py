"""Declaration of FastAPI router for AiiDA's QueryBuilder."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.orm.implementation import StorageBackend
from fastapi import APIRouter, Depends, Query, Request

from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.common.responses import JsonApiResponse
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.models.querybuilder import QueryBuilderDict
from aiida_restapi.profiles import get_profile_backend

read_router = APIRouter(prefix='/querybuilder')


@read_router.post(
    '',
    response_class=JsonApiResponse,
    response_model=JsonApiResourceDocument,
    response_model_exclude_none=True,
    responses={
        422: {
            'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError],
            'description': 'Validation Error | Query Builder Error',
        },
    },
)
async def query_builder(
    request: Request,
    query: QueryBuilderDict,
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
    full: t.Annotated[
        bool,
        Query(description='Whether to return full results (minimal=False).'),
    ] = False,
) -> dict[str, t.Any]:
    """Execute a QueryBuilder query based on the provided dictionary."""
    query_dict = query.model_dump()

    limit = query_dict.pop('limit', 10) or 1
    offset = query_dict.get('offset', 0) or 0

    try:
        qb = orm.QueryBuilder(backend=backend, **query_dict)
        total = qb.count()
        qb.limit(limit)
        results = qb.dict()
    except Exception as exception:
        raise QueryBuilderException(str(exception)) from exception

    try:
        normalized_results = {
            'query_id': 'qb-result',
            'results': [normalize_result(result, minimal=not full) for result in results],
        }
    except Exception as exception:
        raise QueryBuilderException(str(exception)) from exception

    return JsonApi.resource(
        request,
        normalized_results,
        resource_identity='query_id',
        resource_type='qb-results',
        backend=backend,
        meta={
            'total': total,
            'page': (offset // limit) + 1,
            'page_size': limit,
        },
    )


ALIAS_MAP = {
    'id': 'pk',
    'dbcomputer_id': 'computer',
    'user_id': 'user',
    'dbnode_id': 'node',
}


def normalize_result(
    result: dict[str, dict[str, t.Any]],
    minimal: bool = True,
) -> dict[str, dict[str, t.Any]]:
    """Serialize any entities in the QueryBuilder result.

    If the result only contains a single projection of the entity, it will be serialized flat.
    Otherwise, the projections will be normalized, serializing any entities under the '*' key
    and mapping DB keys to their public aliases (e.g. 'id' -> 'pk').

    :param result: The QueryBuilder result.
    :type result: dict[str, dict[str, t.Any]]
    :param minimal: Whether to serialize entities in minimal form.
    :type minimal: bool
    :return: The parsed result.
    :rtype: dict[str, dict[str, t.Any]]
    """
    for tag, projections in result.items():
        if len(projections) == 1 and '*' in projections:
            result[tag] = projections['*'].serialize(minimal=minimal)
            continue

        normalized: dict[str, dict[str, t.Any]] = {}
        for key, projection in projections.items():
            if key == '*':
                normalized[key] = projection.serialize(minimal=minimal)
            else:
                normalized[ALIAS_MAP.get(key, key)] = projection
        result[tag] = normalized

    return result
