"""Pydantic models for QueryBuilder requests and path items."""

from __future__ import annotations

import typing as t

import pydantic as pdt


class QueryBuilderPathItem(pdt.BaseModel):
    """Pydantic model for QueryBuilder path items."""

    entity_type: str | list[str] = pdt.Field(
        description='The AiiDA entity type.',
        examples=['group.core', ['data.core.int.Int.', 'data.core.float.Float.']],
    )
    orm_base: str = pdt.Field(
        description='The ORM base class of the entity.',
        examples=['node', 'computer', 'user'],
    )
    tag: str | None = pdt.Field(
        None,
        description='An optional tag for the path item.',
        examples=['my_nodes'],
    )
    joining_keyword: str | None = pdt.Field(
        None,
        description='The joining keyword for relationships (e.g., "input", "output").',
        examples=['with_group', 'with_user'],
    )
    joining_value: str | None = pdt.Field(
        None,
        description='The joining value for relationships (e.g., "input", "output").',
        examples=['my_group', 'admin'],
    )
    edge_tag: str | None = pdt.Field(
        None,
        description='An optional tag for the edge.',
        examples=['edge_to_group'],
    )
    outerjoin: bool = pdt.Field(
        False,
        description='Whether to perform an outer join.',
        examples=[True],
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
