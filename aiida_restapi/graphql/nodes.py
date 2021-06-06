# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA nodes."""
# pylint: disable=redefined-builtin,too-few-public-methods,unused-argument
from typing import Any, Dict, List, Optional

import graphene as gr
from aiida import orm

from aiida_restapi.graphql.plugins import QueryPlugin

from .comments import CommentsQuery
from .logs import LogsQuery
from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .utils import JSON, parse_date


class NodeQuery(
    single_cls_factory(orm.nodes.Node, exclude_fields=("attributes", "extras"))  # type: ignore[misc]
):
    """Query an AiiDA Node"""

    attributes = JSON(
        description="Variable attributes of the node",
        filter=gr.List(
            gr.String,
            description="return an exact set of attributes keys (non-existent will return null)",
        ),
    )
    extras = JSON(
        description="Variable extras (unsealed) of the node",
        filter=gr.List(
            gr.String,
            description="return an exact set of extras keys (non-existent will return null)",
        ),
    )
    Comments = gr.Field(CommentsQuery)

    @staticmethod
    def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
        """Resolution function."""
        # pass filter specification to CommentsQuery
        filters = {}
        filters["dbnode_id"] = parent["id"]
        return {"filters": filters}

    Logs = gr.Field(LogsQuery)

    @staticmethod
    def resolve_Logs(parent: Any, info: gr.ResolveInfo) -> dict:
        """Resolution function."""
        # pass filter specification to CommentsQuery
        filters = {}
        filters["dbnode_id"] = parent["id"]
        return {"filters": filters}

    # TODO it would be ideal if the attributes/extras were filtered via the SQL query

    @staticmethod
    def resolve_attributes(
        parent: Any, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Resolution function."""
        attributes = parent.get("attributes")
        if filter is None or attributes is None:
            return attributes
        return {key: attributes.get(key) for key in filter}

    @staticmethod
    def resolve_extras(
        parent: Any, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Resolution function."""
        extras = parent.get("extras")
        if filter is None or extras is None:
            return extras
        return {key: extras.get(key) for key in filter}


class NodesQuery(multirow_cls_factory(NodeQuery, orm.nodes.Node, "nodes")):  # type: ignore[misc]
    """Query all AiiDA Nodes"""

    @staticmethod
    def get_filter_kwargs() -> Dict[str, gr.Scalar]:
        """Return a mapping of parameters to filter fields."""
        return dict(
            after=gr.String(
                description="Earliest modified time (allows most known formats to represent a date and/or time)"
            ),
            before=gr.String(
                description="Latest modified time (allows most known formats to represent a date and/or time)"
            ),
            created_after=gr.String(
                description="Earliest created time (allows most known formats to represent a date and/or time)"
            ),
            created_before=gr.String(
                description="Latest created time (allows most known formats to represent a date and/or time)"
            ),
        )

    @staticmethod
    def create_nodes_filter(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Given keyword arguments from the resolver,
        create a filter dictionary to parse to the ``QueryBuilder``."""

        after = kwargs.get("after")
        before = kwargs.get("before")
        created_after = kwargs.get("created_after")
        created_before = kwargs.get("created_before")

        filters: Dict[str, Any] = {}
        if after is not None and before is not None:
            filters["mtime"] = {
                "and": [{">": parse_date(after)}, {"<": parse_date(before)}]
            }
        elif after is not None:
            filters["mtime"] = {">": parse_date(after)}
        elif before is not None:
            filters["mtime"] = {"<": parse_date(before)}

        if created_after is not None and created_before is not None:
            filters["ctime"] = {
                "and": [
                    {">": parse_date(created_after)},
                    {"<": parse_date(created_before)},
                ]
            }
        elif created_after is not None:
            filters["ctime"] = {">": parse_date(created_after)}
        elif created_before is not None:
            filters["ctime"] = {"<": parse_date(created_before)}
        return filters


def resolve_Node(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(orm.nodes.Node, info, id)


def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs: Any) -> dict:
    """Resolution function."""
    # pass filter to NodesQuery
    return {"filters": NodesQuery.create_nodes_filter(kwargs)}


NodeQueryPlugin = QueryPlugin(
    "Node", gr.Field(NodeQuery, id=gr.Int(required=True)), resolve_Node
)
NodesQueryPlugin = QueryPlugin(
    "Nodes", gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs()), resolve_Nodes
)
