"""REST API query utilities."""

from __future__ import annotations

import json
import typing as t

import pydantic as pdt
from fastapi import HTTPException, Query


class QueryParams(pdt.BaseModel):
    filters: dict[str, t.Any] = {}
    order_by: t.Optional[list[str]] = None
    page_size: int = 10
    page: int = 1


def query_params(
    # Filters as free-form JSON object, or individual key=value pairs
    filters: str | None = Query(None, description='AiiDA QueryBuilder filters as JSON string'),
    order_by: str | None = Query(None, description='Comma-separated list of fields to sort by'),
    page_size: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
) -> QueryParams:
    """Parse query parameters into a structured object.

    :param filters: AiiDA QueryBuilder filters as JSON string.
    :param order_by: Comma-separated string of fields to sort by.
    :param page_size: Number of results per page.
    :param page: Page number.
    :return: Structured query parameters.
    :raises HTTPException: If filters cannot be parsed as JSON.
    """
    filter_dict: dict[str, t.Any] = {}
    if filters:
        try:
            filter_dict = json.loads(filters)
        except Exception as exception:
            raise HTTPException(
                status_code=400,
                detail=f'Could not parse filters as JSON: {exception}',
            ) from exception
    order_by_list = [f.strip() for f in order_by.split(',')] if order_by else None
    return QueryParams(
        filters=filter_dict,
        order_by=order_by_list,
        page_size=page_size,
        page=page,
    )
