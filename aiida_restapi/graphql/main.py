# -*- coding: utf-8 -*-
"""Main module that generates the full Graphql App."""
import graphene as gr
from starlette.graphql import GraphQLApp

from .basic import aiidaVersionPlugin, rowLimitMaxPlugin
from .comments import CommentQueryPlugin, CommentsQueryPlugin
from .computers import ComputerQueryPlugin, ComputersQueryPlugin
from .entry_points import aiidaEntryPointGroupsPlugin, aiidaEntryPointsPlugin
from .groups import GroupQueryPlugin, GroupsQueryPlugin
from .logs import LogQueryPlugin, LogsQueryPlugin
from .nodes import NodeQueryPlugin, NodesQueryPlugin
from .plugins import create_query
from .users import UserQueryPlugin, UsersQueryPlugin

Query = create_query(
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


app = GraphQLApp(schema=gr.Schema(query=Query, auto_camelcase=False))
