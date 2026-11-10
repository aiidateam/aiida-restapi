"""Parsing and validation for JSON:API sort query parameters."""

from __future__ import annotations

import typing as t

from aiida.common.exceptions import InputValidationError

from .utils import parse_csv


def parse_sort(raw: str | None) -> dict[str, t.Literal['asc', 'desc']]:
    """Parse a comma-separated sort parameter.

    :param raw: Comma-separated fields, optionally prefixed with ``-`` for descending order.
    :return: A mapping of sort fields to their directions.
    :rtype: dict[str, t.Literal['asc', 'desc']]
    :raises InputValidationError: If a sort field is malformed.
    """
    order_by: dict[str, t.Literal['asc', 'desc']] = {}
    for field in parse_csv(raw) if raw else []:
        direction: t.Literal['asc', 'desc'] = 'desc' if field.startswith('-') else 'asc'
        name = field[1:] if field.startswith(('-', '+')) else field
        if not name or name.startswith(('-', '+')) or any(character.isspace() for character in name):
            raise InputValidationError(f'Invalid sort field: {field!r}.')
        order_by[name] = direction
    return order_by
