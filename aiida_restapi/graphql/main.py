# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin,unused-argument,too-few-public-methods,missing-function-docstring
from typing import Any, Dict, List, Optional

import aiida
import graphene as gr
from aiida import orm
from aiida.plugins.entry_point import (
    ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP,
    get_entry_point_names,
)
from starlette.graphql import GraphQLApp

from .comments import CommentQuery, CommentsQuery
from .computers import ComputerQuery, ComputersQuery
from .config import ENTITY_LIMIT
from .groups import GroupQuery, GroupsQuery
from .logs import LogQuery, LogsQuery
from .nodes import NodeQuery, NodesQuery
from .orm_factories import ENTITY_DICT_TYPE, resolve_entity
from .users import UserQuery, UsersQuery


class EntryPoints(gr.ObjectType):
    group = gr.String()
    names = gr.List(gr.String)


class Query(gr.ObjectType):
    """The top-level query."""

    rowLimitMax = gr.Int(
        description="Maximum amount of entity rows you are allowed to return from a query"
    )

    @staticmethod
    def resolve_rowLimitMax(parent: Any, info: gr.ResolveInfo) -> int:
        return ENTITY_LIMIT

    aiidaVersion = gr.String(description="Version of aiida-core")

    @staticmethod
    def resolve_aiidaVersion(parent: Any, info: gr.ResolveInfo) -> str:
        return aiida.__version__

    aiidaEntryPointGroups = gr.List(
        gr.String, description="List of the entrypoint groups"
    )

    @staticmethod
    def resolve_aiidaEntryPointGroups(parent: Any, info: gr.ResolveInfo) -> List[str]:
        return list(ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP.keys())

    aiidaEntryPoints = gr.Field(
        EntryPoints,
        description="List of the entrypoints in a groups",
        group=gr.String(required=True),
    )

    @staticmethod
    def resolve_aiidaEntryPoints(
        parent: Any, info: gr.ResolveInfo, group: str
    ) -> Dict[str, Any]:
        return {"group": group, "names": get_entry_point_names(group)}

    User = gr.Field(UserQuery, id=gr.Int(required=True))

    @staticmethod
    def resolve_User(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.User, info, id)

    Users = gr.Field(UsersQuery)

    @staticmethod
    def resolve_Users(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to UsersQuery
        return {}

    Computer = gr.Field(ComputerQuery, id=gr.Int(required=True))

    @staticmethod
    def resolve_Computer(
        parent: Any, info: gr.ResolveInfo, id: int
    ) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Computer, info, id)

    Computers = gr.Field(ComputersQuery)

    @staticmethod
    def resolve_Computers(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to ComputersQuery
        return {}

    Node = gr.Field(
        NodeQuery,
        id=gr.Int(required=True),
    )

    @staticmethod
    def resolve_Node(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.nodes.Node, info, id)

    Nodes = gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter to NodesQuery
        return {"filters": NodesQuery.create_nodes_filter(kwargs)}

    Comment = gr.Field(CommentQuery, id=gr.Int(required=True))

    @staticmethod
    def resolve_Comment(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Comment, info, id)

    Comments = gr.Field(CommentsQuery)

    @staticmethod
    def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to CommentsQuery
        return {}

    Log = gr.Field(LogQuery, id=gr.Int(required=True))

    @staticmethod
    def resolve_Log(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Log, info, id)

    Logs = gr.Field(LogsQuery)

    @staticmethod
    def resolve_Logs(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to LogsQuery
        return {}

    Group = gr.Field(GroupQuery, id=gr.Int(required=True))

    @staticmethod
    def resolve_Group(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Group, info, id)

    Groups = gr.Field(GroupsQuery)

    @staticmethod
    def resolve_Groups(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to GroupsQuery
        return {}


app = GraphQLApp(schema=gr.Schema(query=Query, auto_camelcase=False))
