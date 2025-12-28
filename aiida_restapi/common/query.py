"""REST API query utilities."""

from __future__ import annotations

import json
import typing as t

import pydantic as pdt


class QueryParams(pdt.BaseModel):
    filters: dict[str, t.Any] | None = pdt.Field(
        None,
        description='AiiDA QueryBuilder filters',
        examples=[
            '{"node_type": "data.core.int.Int."}',
            '{"attributes.value": {">": 42}}',
        ],
    )
    order_by: str | list[str] | dict[str, t.Any] | None = pdt.Field(
        None,
        description='Fields to sort by',
        examples=[
            'pk',
            'uuid,label',
            '{"attributes.value": "desc"}',
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

    @pdt.field_validator('filters', mode='before')
    @classmethod
    def parse_filters(cls, value: t.Any) -> dict[str, t.Any] | None:
        if value:
            try:
                return json.loads(value)
            except Exception as exception:
                raise ValueError(f'Could not parse filters as JSON: {exception}') from exception
        return None

    @pdt.field_validator('order_by', mode='before')
    @classmethod
    def parse_order_by(cls, value: t.Any) -> str | list[str] | dict[str, t.Any] | None:
        if value:
            # Due to allowing list[str] on the field, FastAPI will always convert query to a list
            raw: str = value[0]
            if raw.startswith('{') or raw.startswith('['):
                try:
                    return json.loads(raw)
                except Exception as exception:
                    raise ValueError(f'Could not parse order_by as JSON: {exception}') from exception
            return raw.split(',')
        return None
