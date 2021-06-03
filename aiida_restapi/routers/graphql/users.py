# -*- coding: utf-8 -*-
from typing import Any

import graphene as gr
from aiida.orm import User

from .nodes import NodesEntity, create_nodes_filter, nodes_filter_kwargs
from .utils import make_entities_cls


class UserEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)", required=True)
    email = gr.ID(description="Email address of the user")
    first_name = gr.String(description="First name of the user")
    last_name = gr.String(description="Last name of the user")
    institution = gr.String(description="Host institution or workplace of the user")
    Nodes = gr.Field(NodesEntity, **nodes_filter_kwargs)

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesEntity
        filters = create_nodes_filter(kwargs)
        filters["user_id"] = parent["id"]
        return {"filters": filters}


class UsersEntity(make_entities_cls(UserEntity, User, "users")):
    """A list of users"""
