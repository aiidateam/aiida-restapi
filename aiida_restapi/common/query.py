"""REST API query utilities."""

from __future__ import annotations

import json
import re
import typing as t

import pydantic as pdt
from aiida.common.exceptions import InputValidationError
from fastapi import Depends, Query, Request

__all__ = [
    'CollectionQueryParams',
    'QueryParams',
    'ResourceQueryParams',
    'collection_query_params',
    'query_parameter_items',
    'querybuilder_params',
    'resource_query_params',
]


class Filtering(pdt.BaseModel):
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
    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        default=None,
        description='Fields to sort by',
        examples=[
            'ctime',
            ['label', '-ctime'],
        ],
    )


class Pagination(pdt.BaseModel):
    limit: pdt.PositiveInt = pdt.Field(
        default=10,
        description='Number of results per page',
        examples=[10],
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


class QueryParams(Filtering, Sorting, Pagination):
    """QueryBuilder parameters: filters, sorting, pagination."""

    query_items: list[tuple[str, str]] = pdt.Field(default_factory=list, exclude=True)


class CollectionQueryParams(QueryParams, Include):
    """Query parameters for a collection resource: filters, sorting, pagination, include."""


class ResourceQueryParams(Include):
    """Query parameters for a single resource: include."""


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(',') if item.strip()]


def _parse_filter_value(raw: str) -> t.Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


_FILTER_KEY = re.compile(r'filter\[([^][\s]+)\](?:\[([^][\s]+)\])?')
_TRUNCATED_OPERATOR_KEY = re.compile(r'filter\[[^][\s]+\]\[!?[<>=]*')

_GENERAL_OPS = {
    '==',
    '!==',
    'in',
}

_NUMERIC_OPS = {
    '<',
    '<=',
    '>',
    '>=',
}

_STRING_OPS = {
    'like',
    'ilike',
}

_ARRAY_OPS = {
    'contains',
    'of_length',
    'shorter',
    'longer',
}

_DICT_OPS = {
    'has_key',
}

_FILTER_OPERATORS = {
    *_GENERAL_OPS,
    *_NUMERIC_OPS,
    *_STRING_OPS,
    *_ARRAY_OPS,
    *_DICT_OPS,
}


def query_parameter_items(request: Request) -> list[tuple[str, str]]:
    """Return decoded query items, repairing comparison operators split at their equals sign."""
    items: list[tuple[str, str]] = []
    for key, value in request.query_params.multi_items():
        normalized_key = key
        normalized_value = value
        if _TRUNCATED_OPERATOR_KEY.fullmatch(key):
            operator_remainder, separator, operand = value.partition(']=')
            if separator:
                normalized_key = f'{key}={operator_remainder}]'
                normalized_value = operand
        items.append((normalized_key, normalized_value))
    return items


def _parse_filter_list(operator: str, raw: str) -> list[t.Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exception:
        raise InputValidationError(f'The `{operator}` filter requires a JSON list.') from exception
    if not isinstance(value, list):
        raise InputValidationError(f'The `{operator}` filter requires a JSON list.')
    if not value:
        raise InputValidationError(f'The `{operator}` filter requires at least one value.')
    return value


def _parse_filter_operator(operator: str | None) -> str:
    if operator is None:
        return '=='
    positive_operator = operator[1:] if operator.startswith('!') else operator
    if positive_operator in _FILTER_OPERATORS:
        return operator
    raise InputValidationError(f'Invalid filter operator: {operator!r}.')


def _parse_filter_operand(operator: str, raw: str) -> t.Any:
    positive_operator = operator.lstrip('!~')
    if positive_operator in {'in', 'contains'}:
        return _parse_filter_list(positive_operator, raw)
    value = _parse_filter_value(raw)
    if positive_operator in _NUMERIC_OPS and not isinstance(value, (int, float)):
        raise InputValidationError(f'The `{positive_operator}` filter requires a numeric value.')
    if positive_operator in _STRING_OPS and not isinstance(value, str):
        raise InputValidationError(f'The `{positive_operator}` filter requires a string value.')
    if positive_operator in _ARRAY_OPS and not isinstance(value, int):
        raise InputValidationError(f'The `{positive_operator}` filter requires an integer value.')
    return value


def _parse_filters(query_items: list[tuple[str, str]]) -> dict[str, t.Any]:
    expressions: dict[str, list[dict[str, t.Any]]] = {}
    for key, raw in query_items:
        if not key.startswith('filter'):
            continue
        match = _FILTER_KEY.fullmatch(key)
        if match is None:
            raise InputValidationError(f'Invalid filter parameter: {key!r}.')
        field, raw_operator = match.groups()
        operator = _parse_filter_operator(raw_operator)
        operand = _parse_filter_operand(operator, raw)
        expressions.setdefault(field, []).append({operator: operand})

    filters: dict[str, t.Any] = {}
    for field, field_expressions in expressions.items():
        normalized_expressions = field_expressions
        for membership_operator in ('in', '!in'):
            membership = [
                expression[membership_operator]
                for expression in normalized_expressions
                if membership_operator in expression
            ]
            if len(membership) > 1:
                normalized_expressions = [
                    expression for expression in normalized_expressions if membership_operator not in expression
                ] + [{membership_operator: [item for values in membership for item in values]}]
        filters[field] = (
            normalized_expressions[0] if len(normalized_expressions) == 1 else {'and': normalized_expressions}
        )

    return filters


def _parse_sort(raw: str | None) -> dict[str, t.Literal['asc', 'desc']]:
    order_by: dict[str, t.Literal['asc', 'desc']] = {}
    for field in _parse_csv(raw) if raw else []:
        direction: t.Literal['asc', 'desc'] = 'desc' if field.startswith('-') else 'asc'
        name = field[1:] if field.startswith(('-', '+')) else field
        if not name or name.startswith(('-', '+')) or any(character.isspace() for character in name):
            raise InputValidationError(f'Invalid sort field: {field!r}.')
        order_by[name] = direction
    return order_by


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
    """Parse JSON:API filtering, sorting, and pagination parameters."""
    query_items = query_parameter_items(request)
    return QueryParams(
        filters=_parse_filters(query_items),
        order_by=_parse_sort(sort),
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
    """Dependency to parse include parameters.

    :param include: Comma-separated string of JSON:API include paths.
    :type include: str | None
    :return: Structured include parameters.
    :rtype: Include
    """
    return Include(include=_parse_csv(include) if include else [])


def collection_query_params(
    query_params: t.Annotated[QueryParams, Depends(querybuilder_params)],
    include: t.Annotated[Include, Depends(include_params)],
) -> CollectionQueryParams:
    """Dependency to parse collection query parameters.

    :param query_params: The query builder parameters.
    :type query_params: QueryParams
    :param include: The include parameters.
    :type include: Include
    :return: The combined collection query parameters.
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
    """Dependency to parse resource query parameters.

    :param include: The include parameters.
    :type include: Include
    :return: The resource query parameters.
    :rtype: ResourceQueryParams
    """
    return ResourceQueryParams(**include.model_dump())
