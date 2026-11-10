"""Pydantic models for parsed query parameters."""

from __future__ import annotations

import typing as t

import pydantic as pdt


class Filtering(pdt.BaseModel):
    """Parsed AiiDA QueryBuilder filters."""

    filters: dict[str, t.Any] = pdt.Field(
        default_factory=dict,
        description='AiiDA QueryBuilder filters',
        examples=[
            'filter[node_type]=data.core.int.Int.',
            'filter[pk][in]=[1,10,100]',
            'filter[attributes.value][<=]=42',
            'filter[label][like]=%test%',
            'filter[attributes.some_array][contains]=[1,True,"hello"]',
            'filter[attributes.some_dict][has_key]=some_key',
        ],
    )


class Sorting(pdt.BaseModel):
    """Parsed sort order."""

    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        default=None,
        description='Fields to sort by',
        examples=[
            'ctime',
            ['label', '-ctime'],
        ],
    )


class Include(pdt.BaseModel):
    """Parsed JSON:API include paths."""

    include: list[str] = pdt.Field(
        default_factory=list,
        description='Related resource types to include',
        examples=[
            'nodes',
            'users,computers',
        ],
    )


class Pagination(pdt.BaseModel):
    """Offset/limit pagination request."""

    limit: pdt.PositiveInt = pdt.Field(
        default=10,
        description='Number of results per page',
        examples=[10],
    )
    offset: pdt.NonNegativeInt = pdt.Field(
        default=0,
        description='Number of results to skip',
        examples=[0],
    )


class QueryParams(Filtering, Sorting, Pagination):
    """Filtering, sorting, and pagination parameters for a collection query."""

    query_items: list[tuple[str, str]] = pdt.Field(default_factory=list, exclude=True)


class CollectionQueryParams(QueryParams, Include):
    """Collection query parameters, including requested related resources."""


class ResourceQueryParams(Include):
    """Query parameters for a single resource."""
