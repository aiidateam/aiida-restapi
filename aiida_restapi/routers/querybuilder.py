"""Declaration of FastAPI router for AiiDA's QueryBuilder."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Query

from aiida_restapi.common import errors
from aiida_restapi.common.exceptions import QueryBuilderException
from aiida_restapi.common.pagination import PaginatedResults
from aiida_restapi.models.querybuilder import QueryBuilderDict

read_router = APIRouter(prefix='/querybuilder')


@read_router.post(
    '',
    response_model=PaginatedResults,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    responses={
        422: {'model': t.Union[errors.RequestValidationError, errors.QueryBuilderError]},
    },
)
@with_dbenv()
async def query_builder(
    query: QueryBuilderDict,
    flat: bool = Query(
        False,
        description='Whether to return results flat.',
    ),
) -> PaginatedResults:
    """Execute a QueryBuilder query based on the provided dictionary."""
    query_dict = query.model_dump()

    try:
        limit = query_dict.pop('limit', 10)
        offset = query_dict.get('offset', 0)

        # Get total count before applying the limit
        qb = orm.QueryBuilder.from_dict(query_dict)
        total = qb.count()
        qb.limit(limit)

        # Run query builder
        project = t.cast(dict, query_dict.get('project'))
        if not project or any(p in ('*', ['*']) for p in project.values()):
            # Projecting entities as entity models
            return PaginatedResults[orm.Entity.Model](
                total=total,
                page=offset // limit + 1,
                page_size=limit,
                data=[entity.to_model(minimal=True) for entity in t.cast(list[orm.Entity], qb.all(flat=True))],
            )
        else:
            # Projecting specific attributes
            return PaginatedResults[t.Any](
                total=total,
                page=offset // limit + 1,
                page_size=limit,
                data=qb.all(flat=flat),
            )

    except Exception as exception:
        raise QueryBuilderException(str(exception)) from exception
