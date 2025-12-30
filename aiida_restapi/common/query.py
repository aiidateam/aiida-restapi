"""REST API query utilities."""

from __future__ import annotations

import json
import typing as t

import pydantic as pdt
from fastapi import Depends, Query

__all__ = [
    'CollectionQueryParams',
    'QueryBuilderParams',
    'ResourceQueryParams',
    'collection_query_params',
    'querybuilder_params',
    'resource_query_params',
]


class Filtering(pdt.BaseModel):
    filters: dict[str, t.Any] = pdt.Field(
        default_factory=dict,
        description='AiiDA QueryBuilder filters',
        examples=[
            {'node_type': {'==': 'data.core.int.Int.'}},
            {'attributes.value': {'>': 42}},
        ],
    )


class Sorting(pdt.BaseModel):
    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        default=None,
        description='Fields to sort by',
        examples=[
            {'attributes.value': 'desc'},
        ],
    )


class Pagination(pdt.BaseModel):
    page_size: pdt.PositiveInt = pdt.Field(
        default=10,
        description='Number of results per page',
        examples=[10],
    )
    page: pdt.PositiveInt = pdt.Field(
        default=1,
        description='Page number',
        examples=[1],
    )
    offset: pdt.NonNegativeInt = pdt.Field(
        default=0,
        description='Offset for results',
        examples=[0],
    )


class Include(pdt.BaseModel):
    include: list[str] = pdt.Field(
        default_factory=list,
        description='Related resources to include',
        examples=[
            'nodes',
            'users,computers',
        ],
    )


class QueryBuilderParams(Filtering, Sorting, Pagination):
    """QueryBuilder parameters: filters, sorting, pagination."""


class CollectionQueryParams(QueryBuilderParams, Include):
    """Query parameters for a collection resource: filters, sorting, pagination, include."""


class ResourceQueryParams(Include):
    """Query parameters for a single resource: include."""


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(',') if item.strip()]


def querybuilder_params(
    filters: t.Annotated[
        str | None,
        Query(description='AiiDA QueryBuilder filters as JSON string or object'),
    ] = None,
    order_by: t.Annotated[
        str | None,
        Query(description='Fields to sort by, as a comma-separated string, JSON array, or JSON object'),
    ] = None,
    page_size: t.Annotated[
        int,
        Query(ge=1, description='Number of results per page'),
    ] = 10,
    page: t.Annotated[
        int,
        Query(ge=1, description='Page number'),
    ] = 1,
    offset: t.Annotated[
        int,
        Query(ge=0, description='Offset for results'),
    ] = 0,
) -> QueryBuilderParams:
    """Dependency to parse QueryBuilder parameters.

    :param filters: AiiDA QueryBuilder filters as JSON string.
    :type filters: str | None
    :param order_by: Comma-separated string of fields to sort by.
    :type order_by: str | None
    :param page_size: Number of results per page.
    :type page_size: int
    :param page: Page number.
    :type page: int
    :return: Structured query parameters.
    :rtype: QueryBuilderParams
    :raises HTTPException: If arguments cannot be parsed as JSON.
    """
    query_filters: dict[str, t.Any] = {}
    if filters:
        query_filters = json.loads(filters)
        if not isinstance(query_filters, dict):
            raise pdt.ValidationError('Filters must be a JSON object')

    query_order_by: str | list[str] | dict[str, t.Any] | None = None
    if order_by:
        if order_by.lstrip().startswith(('{', '[', '"')):
            query_order_by = json.loads(order_by)
        else:
            query_order_by = _parse_csv(order_by)

    return QueryBuilderParams(
        filters=query_filters,
        order_by=query_order_by,
        page_size=page_size,
        page=page,
        offset=offset,
    )


def include_params(
    include: t.Annotated[
        str | None,
        Query(description='JSON:API include paths as a comma-separated string'),
    ] = None,
) -> Include:
    """Dependency to parse include parameters.

    :param include: Comma-separated string of JSON:API include paths.
    :type include: str | None
    :return: Structured include parameters.
    :rtype: Include
    """
    return Include(include=_parse_csv(include) if include else [])


def collection_query_params(
    qb_params: t.Annotated[QueryBuilderParams, Depends(querybuilder_params)],
    include: t.Annotated[Include, Depends(include_params)],
) -> CollectionQueryParams:
    """Dependency to parse collection query parameters.

    :param qb_params: The query builder parameters.
    :type qb_params: QueryBuilderParams
    :param include: The include parameters.
    :type include: Include
    :return: The combined collection query parameters.
    :rtype: CollectionQueryParams
    """
    return CollectionQueryParams(**qb_params.model_dump(), **include.model_dump())


def resource_query_params(
    include: t.Annotated[Include, Depends(include_params)],
) -> ResourceQueryParams:
    """Dependency to parse resource query parameters.

    :param include: The include parameters.
    :type include: Include
    :return: The resource query parameters.
    :rtype: ResourceQueryParams
    """
    return ResourceQueryParams(**include.model_dump())
