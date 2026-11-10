"""Parsing and validation for JSON:API filter query parameters.

JSON:API provides the `filter` query parameter but no further semantics. The implementation is left
to the server. Here, we implement a convention that mirrors the AiiDA `QueryBuilder` implementation.
"""

from __future__ import annotations

import json
import re
import typing as t

from aiida.common.exceptions import InputValidationError
from starlette.requests import Request

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


def get_query_parameter_items(request: Request) -> list[tuple[str, str]]:
    """Return decoded query items, repairing comparison operators split at their equals sign.

    :param request: The HTTP request to read query items from.
    :return: Query key/value pairs with filter operators reconstructed.
    :rtype: list[tuple[str, str]]
    """
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


def parse_filters(query_items: list[tuple[str, str]]) -> dict[str, t.Any]:
    """Parse filter query items into QueryBuilder filter expressions.

    :param query_items: Decoded query key/value pairs.
    :return: QueryBuilder filters grouped by field.
    :rtype: dict[str, t.Any]
    :raises InputValidationError: If a filter key, operator, or operand is invalid.
    """
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


def _parse_filter_value(raw: str) -> t.Any:
    """Decode a JSON scalar, falling back to the original string.

    :param raw: The raw query parameter value.
    :return: The decoded JSON value or original string.
    :rtype: t.Any
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _parse_filter_list(operator: str, raw: str) -> list[t.Any]:
    """Parse and validate a non-empty JSON list operand.

    :param operator: The list operator being applied.
    :param raw: The raw JSON query parameter value.
    :return: The parsed list operand.
    :rtype: list[t.Any]
    :raises InputValidationError: If the value is invalid JSON, not a list, or empty.
    """
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
    """Validate an explicit filter operator or apply the default equality operator.

    :param operator: The operator supplied in the filter key, if any.
    :return: The validated operator.
    :rtype: str
    :raises InputValidationError: If the operator is not supported.
    """
    if operator is None:
        return '=='
    positive_operator = operator[1:] if operator.startswith('!') else operator
    if positive_operator in _FILTER_OPERATORS:
        return operator
    raise InputValidationError(f'Invalid filter operator: {operator!r}.')


def _parse_filter_operand(operator: str, raw: str) -> t.Any:
    """Parse an operand and validate its type for the selected operator.

    :param operator: The validated filter operator.
    :param raw: The raw query parameter value.
    :return: The parsed operand.
    :rtype: t.Any
    :raises InputValidationError: If the operand has an invalid type or shape.
    """
    positive_operator = operator.lstrip('!~')
    if positive_operator in {'in', 'contains'}:
        return _parse_filter_list(positive_operator, raw)
    value = _parse_filter_value(raw)
    if positive_operator in _NUMERIC_OPS and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise InputValidationError(f'The `{positive_operator}` filter requires a numeric value.')
    if positive_operator in _STRING_OPS and not isinstance(value, str):
        raise InputValidationError(f'The `{positive_operator}` filter requires a string value.')
    if positive_operator in _ARRAY_OPS and (isinstance(value, bool) or not isinstance(value, int)):
        raise InputValidationError(f'The `{positive_operator}` filter requires an integer value.')
    return value
