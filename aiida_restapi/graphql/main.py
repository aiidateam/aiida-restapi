# -*- coding: utf-8 -*-
"""Main module that generates the full Graphql App."""
from starlette_graphene3 import GraphQLApp

from .basic import aiidaVersionPlugin, rowLimitMaxPlugin
from .comments import CommentQueryPlugin, CommentsQueryPlugin
from .computers import ComputerQueryPlugin, ComputersQueryPlugin
from .entry_points import aiidaEntryPointGroupsPlugin, aiidaEntryPointsPlugin
from .groups import GroupQueryPlugin, GroupsQueryPlugin
from .logs import LogQueryPlugin, LogsQueryPlugin
from .nodes import NodeQueryPlugin, NodesQueryPlugin
from .plugins import create_schema
from .users import UserQueryPlugin, UsersQueryPlugin

SCHEMA = create_schema(
    [
        rowLimitMaxPlugin,
        aiidaVersionPlugin,
        aiidaEntryPointGroupsPlugin,
        aiidaEntryPointsPlugin,
        CommentQueryPlugin,
        CommentsQueryPlugin,
        ComputerQueryPlugin,
        ComputersQueryPlugin,
        GroupQueryPlugin,
        GroupsQueryPlugin,
        LogQueryPlugin,
        LogsQueryPlugin,
        NodeQueryPlugin,
        NodesQueryPlugin,
        UserQueryPlugin,
        UsersQueryPlugin,
    ]
)


app = GraphQLApp(schema=SCHEMA)
