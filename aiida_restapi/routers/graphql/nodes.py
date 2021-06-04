# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin,unused-argument,too-few-public-methods,missing-function-docstring
from typing import Any, Dict, List, Optional

import graphene as gr
from aiida import orm

from .comments import CommentsEntity
from .utils import JSON, make_entities_cls, parse_date


class NodeEntity(gr.ObjectType):
    id = gr.Int(description="Unique id (pk)")
    uuid = gr.ID(description="Unique uuid")
    node_type = gr.String(description="Node type")
    process_type = gr.String(description="Process type")
    label = gr.String(description="Label of node")
    description = gr.String(description="Description of node")
    ctime = gr.DateTime(description="Creation time")
    mtime = gr.DateTime(description="Last modification time")
    user_id = gr.Int(description="Created by user id (pk)")
    dbcomputer_id = gr.Int(description="Associated computer id (pk)")
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
    Comments = gr.Field(CommentsEntity)

    @staticmethod
    def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter specification to CommentsEntity
        filters = {}
        filters["dbnode_id"] = parent["id"]
        return {"filters": filters}

    # TODO it would be ideal if the attributes/extras were filtered via the SQL query

    @staticmethod
    def resolve_attributes(
        parent, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ):
        attributes = parent.get("attributes")
        if filter is None or attributes is None:
            return attributes
        return {key: attributes.get(key) for key in filter}

    @staticmethod
    def resolve_extras(
        parent, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ):
        extras = parent.get("extras")
        if filter is None or extras is None:
            return extras
        return {key: extras.get(key) for key in filter}


class NodesEntity(make_entities_cls(NodeEntity, orm.nodes.Node, "nodes")):
    """A list of nodes"""

    @staticmethod
    def get_filter_kwargs():
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
    def create_nodes_filter(kwargs) -> Dict[str, Any]:
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
