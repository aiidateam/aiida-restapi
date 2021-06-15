# -*- coding: utf-8 -*-
"""Main module that generates the full Graphql App."""
# pylint: disable=no-self-use,redefined-builtin,too-many-arguments,too-few-public-methods
from typing import Any, Callable, List, Optional

import graphene as gr
from starlette.concurrency import run_in_threadpool
from starlette.graphql import GraphQLApp

from .basic import aiidaVersionPlugin, rowLimitMaxPlugin
from .comments import CommentQueryPlugin, CommentsQueryPlugin
from .computers import ComputerQueryPlugin, ComputersQueryPlugin
from .entry_points import aiidaEntryPointGroupsPlugin, aiidaEntryPointsPlugin
from .groups import GroupCreatePlugin, GroupQueryPlugin, GroupsQueryPlugin
from .logs import LogQueryPlugin, LogsQueryPlugin
from .nodes import NodeQueryPlugin, NodesQueryPlugin
from .plugins import create_schema
from .users import UserQueryPlugin, UsersQueryPlugin

SCHEMA = create_schema(
    queries=[
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
    ],
    mutations=[GroupCreatePlugin],
)


class GraphQLAppWithMiddleware(GraphQLApp):
    """A GraphQLApp that exposes graphene middleware."""

    def __init__(
        self,
        schema: gr.Schema,
        executor: Any = None,
        executor_class: Optional[type] = None,
        graphiql: bool = True,
        middleware: Optional[List[Any]] = None,
    ) -> None:
        """Initialise GraphQLApp."""
        self.middleware = middleware
        super().__init__(schema, executor, executor_class, graphiql)

    async def execute(  # type: ignore
        self, query, variables=None, context=None, operation_name=None
    ):
        """Execute a query."""
        if self.is_async:
            return await self.schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                executor=self.executor,
                return_promise=True,
                context=context,
                middleware=self.middleware,
            )

        return await run_in_threadpool(
            self.schema.execute,
            query,
            variables=variables,
            operation_name=operation_name,
            context=context,
            middleware=self.middleware,
        )


class AuthorizationMiddleware:
    """GraphQL middleware, to handle authentication of requests."""

    def resolve(
        self, next: Callable[..., Any], root: Any, info: gr.ResolveInfo, **args: Any
    ) -> Any:
        """Run before each field query resolution or mutation"""
        # we can get the header of the request from the context
        if "request" in info.context:
            # print(info.context["request"].headers)
            pass
        # we can then check what type of operation is being performed and act accordingly
        if info.operation.operation == "query":
            # TODO allow only a certain number of queries in a single request?
            pass
        elif info.operation.operation == "mutation":
            # TODO handle authentication via JWT token
            pass
        return next(root, info, **args)


app = GraphQLAppWithMiddleware(schema=SCHEMA, middleware=[AuthorizationMiddleware()])
