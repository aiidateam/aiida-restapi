"""FastAPI dependencies for parsing query parameters."""

from __future__ import annotations

import typing as t

from fastapi import Depends, Query, Request

from .filters import get_query_parameter_items, parse_filters
from .models import CollectionQueryParams, Include, QueryParams, ResourceQueryParams
from .sorting import parse_sort
from .utils import parse_csv


def querybuilder_params(
    request: Request,
    sort: t.Annotated[
        str | None,
        Query(description='Comma-separated fields to sort by; prefix descending fields with `-`'),
    ] = None,
    limit: t.Annotated[
        int,
        Query(alias='page[limit]', ge=1, description='Number of results per page'),
    ] = 10,
    offset: t.Annotated[
        int,
        Query(alias='page[offset]', ge=0, description='Number of results to skip'),
    ] = 0,
) -> QueryParams:
    """Parse JSON:API filtering, sorting, and pagination parameters.

    :param request: The request containing filter parameters.
    :param sort: Comma-separated sort fields; prefix descending fields with ``-``.
    :param limit: Maximum number of results to return.
    :param offset: Number of results to skip.
    :return: Parsed filters, sort order, pagination, and original query items.
    :rtype: QueryParams
    :raises InputValidationError: If a filter or sort parameter is invalid.
    """
    query_items = get_query_parameter_items(request)
    return QueryParams(
        filters=parse_filters(query_items),
        order_by=parse_sort(sort),
        limit=limit,
        offset=offset,
        query_items=query_items,
    )


def include_params(
    include: t.Annotated[
        str | None,
        Query(description='JSON:API include paths as a comma-separated string'),
    ] = None,
) -> Include:
    """Parse JSON:API include paths.

    :param include: Comma-separated related resource names.
    :return: The parsed include paths.
    :rtype: Include
    """
    return Include(include=parse_csv(include) if include else [])


def collection_query_params(
    query_params: t.Annotated[QueryParams, Depends(querybuilder_params)],
    include: t.Annotated[Include, Depends(include_params)],
) -> CollectionQueryParams:
    """Combine query and include parameters for a collection endpoint.

    :param query_params: Parsed filters, sort order, and pagination.
    :param include: Parsed related-resource includes.
    :return: Combined collection query parameters.
    :rtype: CollectionQueryParams
    """
    return CollectionQueryParams(
        **query_params.model_dump(),
        **include.model_dump(),
        query_items=query_params.query_items,
    )


def resource_query_params(
    include: t.Annotated[Include, Depends(include_params)],
) -> ResourceQueryParams:
    """Build query parameters for a single-resource endpoint.

    :param include: Parsed related-resource includes.
    :return: Resource query parameters.
    :rtype: ResourceQueryParams
    """
    return ResourceQueryParams(**include.model_dump())
