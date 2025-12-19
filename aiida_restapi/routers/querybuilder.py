"""Declaration of FastAPI router for AiiDA's QueryBuilder."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, HTTPException, Query

from aiida_restapi.common.pagination import PaginatedResults

read_router = APIRouter()


class QueryBuilderPathItem(pdt.BaseModel):
    """Pydantic model for QueryBuilder path items."""

    entity_type: str | list[str] = pdt.Field(
        description='The AiiDA entity type.',
    )
    orm_base: str = pdt.Field(
        description='The ORM base class of the entity.',
    )
    tag: str | None = pdt.Field(
        None,
        description='An optional tag for the path item.',
    )
    joining_keyword: str | None = pdt.Field(
        None,
        description='The joining keyword for relationships (e.g., "input", "output").',
    )
    joining_value: str | None = pdt.Field(
        None,
        description='The joining value for relationships (e.g., "input", "output").',
    )
    edge_tag: str | None = pdt.Field(
        None,
        description='An optional tag for the edge.',
    )
    outerjoin: bool = pdt.Field(
        False,
        description='Whether to perform an outer join.',
    )


class QueryBuilderDict(pdt.BaseModel):
    """Pydantic model for QueryBuilder POST requests."""

    path: list[str | QueryBuilderPathItem] = pdt.Field(
        description='The QueryBuilder path as a list of entity types or path items.',
        examples=[
            [
                ['data.core.int.Int.', 'data.core.float.Float.'],
                {
                    'entity_type': 'data.core.int.Int.',
                    'orm_base': 'node',
                    'tag': 'integers',
                },
                {
                    'entity_type': ['data.core.int.Int.', 'data.core.float.Float.'],
                    'orm_base': 'node',
                    'tag': 'numbers',
                },
            ]
        ],
    )
    filters: dict[str, dict[str, t.Any]] | None = pdt.Field(
        None,
        description='The QueryBuilder filters as a dictionary mapping tags to filter conditions.',
        examples=[
            {
                'integers': {'attributes.value': {'<': 42}},
            }
        ],
    )
    project: dict[str, str | list[str]] | None = pdt.Field(
        None,
        description='The QueryBuilder projection as a dictionary mapping tags to attributes to project.',
        examples=[
            {
                'integers': ['uuid', 'attributes.value'],
            }
        ],
    )
    limit: pdt.NonNegativeInt | None = pdt.Field(
        10,
        description='The maximum number of results to return.',
        examples=[5],
    )
    offset: pdt.NonNegativeInt | None = pdt.Field(
        0,
        description='The number of results to skip before starting to collect the result set.',
        examples=[0],
    )
    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        None,
        description='The QueryBuilder order_by as a string, list of strings, '
        'or dictionary mapping tags to order conditions.',
        examples=[
            {'integers': {'pk': 'desc'}},
        ],
    )
    distinct: bool = pdt.Field(
        False,
        description='Whether to return only distinct results.',
        examples=[False],
    )


@read_router.post(
    '/querybuilder',
    response_model=PaginatedResults,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def query_builder(
    query: QueryBuilderDict,
    flat: bool = Query(
        False,
        description='Whether to return results flat.',
    ),
) -> PaginatedResults:
    """Execute a QueryBuilder query based on the provided dictionary.

    :param query: The QueryBuilder query dictionary.
    :param flat: Whether to return results flat.
    :return: The results of the QueryBuilder query.
    :raises HTTPException: 400 if the query is invalid.
    """
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
                results=[entity.to_model(minimal=True) for entity in t.cast(list[orm.Entity], qb.all(flat=True))],
            )
        else:
            # Projecting specific attributes
            return PaginatedResults[t.Any](
                total=total,
                page=offset // limit + 1,
                page_size=limit,
                results=qb.all(flat=flat),
            )

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
