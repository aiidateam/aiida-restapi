# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin,unused-argument,too-few-public-methods,missing-function-docstring
from typing import Any, Dict, List, Optional

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from graphene.types.generic import GenericScalar

from .utils import get_projection, parse_date

nodes_filter_kwargs = dict(
    after=gr.String(description="Earliest modified time"),
    before=gr.String(description="Latest modified time"),
    created_after=gr.String(description="Earliest created time"),
    created_before=gr.String(description="Latest created time"),
)


def create_nodes_filter(kwargs) -> Dict[str, Any]:
    after = kwargs.get("after")
    before = kwargs.get("before")
    created_after = kwargs.get("created_after")
    created_before = kwargs.get("created_before")
    filters = {}
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
    attributes = GenericScalar(
        description="Variable attributes of the node",
        filter=gr.List(
            gr.String,
            description="return an exact set of attributes keys (non-existent will return null)",
        ),
    )
    extras = GenericScalar(
        description="Variable extras (unsealed) of the node",
        filter=gr.List(
            gr.String,
            description="return an exact set of extras keys (non-existent will return null)",
        ),
    )

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


class NodesEntity(gr.ObjectType):
    count = gr.Int(description="Total number of nodes")
    rows = gr.List(
        NodeEntity,
        limit=gr.Int(default_value=100, description="Maximum number of rows to return"),
        offset=gr.Int(default_value=0, description="Skip the first n rows"),
    )

    @with_dbenv()
    @staticmethod
    def resolve_count(parent: Any, info: gr.ResolveInfo) -> int:
        try:
            filters = parent.get("filters")
        except AttributeError:
            filters = None
        query = orm.QueryBuilder().append(orm.Node, filters=filters)
        return query.count()

    @with_dbenv()
    @staticmethod
    def resolve_rows(
        parent: Any,
        info: gr.ResolveInfo,
        limit: int,
        offset: int,
    ) -> List[dict]:
        project = get_projection(info)
        try:
            filters = parent.get("filters")
        except AttributeError:
            filters = None

        query = orm.QueryBuilder().append(
            orm.Node, tag="fields", filters=filters, project=project
        )
        query.offset(offset)
        query.limit(limit)
        return [d["fields"] for d in query.dict()]
