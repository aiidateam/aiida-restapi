"""Defines plugins for AiiDA computers."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any, Optional

import graphene as gr
from aiida.orm import Computer

from aiida_restapi.filter_syntax import parse_filter_str
from aiida_restapi.graphql.plugins import QueryPlugin

from .nodes import NodesQuery
from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .utils import FilterString


class ComputerQuery(single_cls_factory(Computer)):  # type: ignore[misc]
    """Query an AiiDA Computer"""

    nodes = gr.Field(NodesQuery, filters=FilterString())

    @staticmethod
    def resolve_nodes(parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None) -> dict:
        """Resolution function."""
        # pass filter specification to NodesQuery
        parsed_filters = parse_filter_str(filters)
        parsed_filters['dbcomputer_id'] = parent['id']
        return {'filters': parsed_filters}


class ComputersQuery(multirow_cls_factory(ComputerQuery, Computer, 'computers')):  # type: ignore[misc]
    """Query all AiiDA Computers"""


def resolve_Computer(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Computer, info, id, uuid)


def resolve_Computers(parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None) -> dict:
    """Resolution function."""
    # pass filter to ComputersQuery
    return {'filters': parse_filter_str(filters)}


ComputerQueryPlugin = QueryPlugin(
    'computer',
    gr.Field(
        ComputerQuery,
        id=gr.Int(),
        uuid=gr.String(),
        description='Query for a single Computer',
    ),
    resolve_Computer,
)
ComputersQueryPlugin = QueryPlugin(
    'computers',
    gr.Field(
        ComputersQuery,
        description='Query for multiple Computers',
        filters=FilterString(),
    ),
    resolve_Computers,
)
