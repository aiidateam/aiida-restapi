# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA computers."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any, Optional

import graphene as gr
from aiida.orm import Computer

from aiida_restapi.graphql.plugins import QueryPlugin

from .nodes import NodesQuery
from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)


class ComputerQuery(single_cls_factory(Computer)):  # type: ignore[misc]
    """Query an AiiDA Computer"""

    Nodes = gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs: Any) -> dict:
        """Resolution function."""
        # pass filter specification to NodesQuery
        filters = NodesQuery.create_nodes_filter(kwargs)
        filters["dbcomputer_id"] = parent["id"]
        return {"filters": filters}


class ComputersQuery(multirow_cls_factory(ComputerQuery, Computer, "computers")):  # type: ignore[misc]
    """Query all AiiDA Computers"""


def resolve_Computer(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Computer, info, id, uuid)


def resolve_Computers(parent: Any, info: gr.ResolveInfo) -> dict:
    """Resolution function."""
    # pass filter to ComputersQuery
    return {}


ComputerQueryPlugin = QueryPlugin(
    "Computer",
    gr.Field(
        ComputerQuery,
        id=gr.Int(),
        uuid=gr.String(),
        description="Query for a single Computer",
    ),
    resolve_Computer,
)
ComputersQueryPlugin = QueryPlugin(
    "Computers",
    gr.Field(ComputersQuery, description="Query for multiple Computers"),
    resolve_Computers,
)
