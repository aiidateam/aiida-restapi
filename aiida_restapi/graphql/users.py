# -*- coding: utf-8 -*-
from typing import Any

import graphene as gr
from aiida.orm import User

from .nodes import NodesQuery
from .orm_factories import multirow_cls_factory, single_cls_factory


class UserQuery(single_cls_factory(User)):
    """An AiiDA User"""

    Nodes = gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesQuery
        filters = NodesQuery.create_nodes_filter(kwargs)
        filters["user_id"] = parent["id"]
        return {"filters": filters}


class UsersQuery(multirow_cls_factory(UserQuery, User, "users")):
    """All AiiDA User"""
