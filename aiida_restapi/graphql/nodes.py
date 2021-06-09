# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA nodes."""
# pylint: disable=redefined-builtin,too-few-public-methods,unused-argument
from typing import Any, Dict, List, Optional

import graphene as gr
from aiida import orm

from aiida_restapi.filter_syntax import parse_filter_str
from aiida_restapi.graphql.plugins import QueryPlugin

from .comments import CommentsQuery
from .logs import LogsQuery
from .orm_factories import (
    ENTITY_DICT_TYPE,
    fields_from_name,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .utils import JSON, FilterString

Link = type("LinkObjectType", (gr.ObjectType,), fields_from_name("Link"))


class LinkQuery(gr.ObjectType):
    """A link and its end node."""

    link = gr.Field(Link)
    # note: we must refer to this query using a string, to prevent circular dependencies
    node = gr.Field("aiida_restapi.graphql.nodes.NodeQuery")


class LinksQuery(multirow_cls_factory(LinkQuery, orm.nodes.Node, "nodes")):  # type: ignore[misc]
    """Query all AiiDA Links."""


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

    Comments = gr.Field(CommentsQuery, description="Comments attached to a node")

    @staticmethod
    def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
        """Resolution function."""
        # pass filter specification to CommentsQuery
        filters = {}
        filters["dbnode_id"] = parent["id"]
        return {"filters": filters}

    Logs = gr.Field(LogsQuery, description="Logs attached to a process node")

    @staticmethod
    def resolve_Logs(parent: Any, info: gr.ResolveInfo) -> dict:
        """Resolution function."""
        # pass filter specification to CommentsQuery
        filters = {}
        filters["dbnode_id"] = parent["id"]
        return {"filters": filters}

    Incoming = gr.Field(
        LinksQuery, description="Query for incoming nodes", filters=FilterString()
    )

    @staticmethod
    def resolve_Incoming(
        parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
    ) -> dict:
        """Resolution function."""
        # pass edge specification to LinksQuery
        return {
            "parent_id": parent["id"],
            "edge_type": "outgoing",
            "project_edge": True,
            "filters": parse_filter_str(filters),
        }

    Outgoing = gr.Field(
        LinksQuery, description="Query for outgoing nodes", filters=FilterString()
    )

    @staticmethod
    def resolve_Outgoing(
        parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
    ) -> dict:
        """Resolution function."""
        # pass edge specification to LinksQuery
        return {
            "parent_id": parent["id"],
            "edge_type": "incoming",
            "project_edge": True,
            "filters": parse_filter_str(filters),
        }

    Ancestors = gr.Field(
        "aiida_restapi.graphql.nodes.NodesQuery",
        description="Query for ancestor nodes",
        filters=FilterString(),
    )

    @staticmethod
    def resolve_Ancestors(
        parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
    ) -> dict:
        """Resolution function."""
        # pass edge specification to LinksQuery
        return {
            "parent_id": parent["id"],
            "edge_type": "descendants",
            "filters": parse_filter_str(filters),
        }

    Descendants = gr.Field(
        "aiida_restapi.graphql.nodes.NodesQuery",
        description="Query for descendant nodes",
        filters=FilterString(),
    )

    @staticmethod
    def resolve_Descendants(
        parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
    ) -> dict:
        """Resolution function."""
        # pass edge specification to LinksQuery
        return {
            "parent_id": parent["id"],
            "edge_type": "ancestors",
            "filters": parse_filter_str(filters),
        }


class NodesQuery(multirow_cls_factory(NodeQuery, orm.nodes.Node, "nodes")):  # type: ignore[misc]
    """Query all AiiDA Nodes"""


def resolve_Node(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(orm.nodes.Node, info, id, uuid)


def resolve_Nodes(
    parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
) -> dict:
    """Resolution function."""
    # pass filter to NodesQuery
    return {"filters": parse_filter_str(filters)}


NodeQueryPlugin = QueryPlugin(
    "Node",
    gr.Field(
        NodeQuery, id=gr.Int(), uuid=gr.String(), description="Query for a single Node"
    ),
    resolve_Node,
)
NodesQueryPlugin = QueryPlugin(
    "Nodes",
    gr.Field(
        NodesQuery, description="Query for multiple Nodes", filters=FilterString()
    ),
    resolve_Nodes,
)
