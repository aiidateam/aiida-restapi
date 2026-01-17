"""REST API query utilities."""

from __future__ import annotations

import json
import typing as t

import pydantic as pdt
from fastapi import Query


class QueryParams(pdt.BaseModel):
    filters: dict[str, t.Any] = pdt.Field(
        default_factory=dict,
        description='AiiDA QueryBuilder filters',
        examples=[
            {'node_type': {'==': 'data.core.int.Int.'}},
            {'attributes.value': {'>': 42}},
        ],
    )
    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        None,
        description='Fields to sort by',
        examples=[
            {'attributes.value': 'desc'},
        ],
    )
    page_size: pdt.PositiveInt = pdt.Field(
        10,
        description='Number of results per page',
        examples=[10],
    )
    page: pdt.PositiveInt = pdt.Field(
        1,
        description='Page number',
        examples=[1],
    )


def query_params(
    filters: str | None = Query(
        None,
        description='AiiDA QueryBuilder filters as JSON string',
    ),
    order_by: str | None = Query(
        None,
        description='Comma-separated list of fields to sort by',
    ),
    page_size: pdt.PositiveInt = Query(
        10,
        description='Number of results per page',
    ),
    page: pdt.PositiveInt = Query(
        1,
        description='Page number',
    ),
) -> QueryParams:
    """Parse query parameters into a structured object.

    :param filters: AiiDA QueryBuilder filters as JSON string.
    :param order_by: Comma-separated string of fields to sort by.
    :param page_size: Number of results per page.
    :param page: Page number.
    :return: Structured query parameters.
    :raises HTTPException: If filters cannot be parsed as JSON.
    """
    query_filters: dict[str, t.Any] = {}
    query_order_by: str | list[str] | dict[str, t.Any] | None = None
    if filters:
        query_filters = json.loads(filters)
    if order_by:
        query_order_by = json.loads(order_by)
    return QueryParams(
        filters=query_filters,
        order_by=query_order_by,
        page_size=page_size,
        page=page,
    )
