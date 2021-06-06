# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA users."""
# pylint: disable=too-few-public-methods,redefined-builtin,unused-argument
from typing import Any

import graphene as gr
from aiida.orm import User

from .nodes import NodesQuery
from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .plugins import QueryPlugin


class UserQuery(single_cls_factory(User)):  # type: ignore[misc]
    """Query an AiiDA User"""

    Nodes = gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs: Any) -> dict:
        """Resolution function."""
        # pass filter specification to NodesQuery
        filters = NodesQuery.create_nodes_filter(kwargs)
        filters["user_id"] = parent["id"]
        return {"filters": filters}


def resolve_User(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(User, info, id)


class UsersQuery(multirow_cls_factory(UserQuery, User, "users")):  # type: ignore[misc]
    """Query all AiiDA Users"""


def resolve_Users(parent: Any, info: gr.ResolveInfo) -> dict:
    """Resolution function."""
    # pass filter to UsersQuery
    return {}


UserQueryPlugin = QueryPlugin(
    "User", gr.Field(UserQuery, id=gr.Int(required=True)), resolve_User
)
UsersQueryPlugin = QueryPlugin("Users", gr.Field(UsersQuery), resolve_Users)
