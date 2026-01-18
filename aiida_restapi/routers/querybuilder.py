"""Declaration of FastAPI router for AiiDA's QueryBuilder."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Query, Request

from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import errors
from aiida_restapi.jsonapi.models.base import JsonApiResourceDocument
from aiida_restapi.jsonapi.responses import JsonApiResponse
from aiida_restapi.models.querybuilder import QueryBuilderDict

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
@with_dbenv()
async def query_builder(
    request: Request,
    query: QueryBuilderDict,
    flat: t.Annotated[
        bool,
        Query(description='Whether to return results flat.'),
    ] = False,
    full: t.Annotated[
        bool,
        Query(description='Whether to return full results (minimal=False).'),
    ] = False,
) -> dict[str, t.Any]:
    """Execute a QueryBuilder query based on the provided dictionary."""
    query_dict = query.model_dump()

    limit = query_dict.pop('limit', 10)
    offset = query_dict.get('offset', 0)

    try:
        qb = orm.QueryBuilder.from_dict(query_dict)
        total = qb.count()
        qb.limit(limit)
        results = qb.all(flat=flat)
    except Exception as exception:
        raise QueryBuilderException(str(exception)) from exception

    if flat:
        parsed = _to_resource_result(results, minimal=not full)
    else:
        parsed = [_to_resource_result(result, minimal=not full) for result in results]

    result = {
        'id': 'qb-result',
        'results': parsed,
    }

    return JsonApi.resource(
        request,
        result,
        resource_identity='id',
        resource_type='qb-results',
        meta={
            'total': total,
            'page': (offset // limit) + 1,
            'page_size': limit,
        },
    )


def _to_resource_result(raw: list[t.Any], minimal: bool = True) -> list[t.Any]:
    """Convert raw QueryBuilder results to JSON:API serializable format.

    :param raw: The raw results from QueryBuilder.
    :type raw: list[t.Any]
    :param minimal: Whether to serialize entities in minimal form.
    :type minimal: bool
    :return: The parsed results.
    :rtype: list[t.Any]
    """
    parsed: list[t.Any] = []
    for item in raw:
        if isinstance(item, orm.Entity):
            parsed.append(item.serialize(minimal=minimal))
        else:
            parsed.append(item)
    return parsed
