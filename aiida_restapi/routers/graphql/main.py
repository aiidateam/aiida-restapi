# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin,unused-argument,too-few-public-methods,missing-function-docstring
from typing import Any, Dict, Optional

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from starlette.graphql import GraphQLApp

from .comments import CommentEntity, CommentsEntity
from .computers import ComputerEntity, ComputersEntity
from .groups import GroupEntity, GroupsEntity
from .nodes import NodeEntity, NodesEntity, create_nodes_filter, nodes_filter_kwargs
from .users import UserEntity, UsersEntity
from .utils import get_projection

ENTITY_DICT_TYPE = Optional[Dict[str, Any]]


@with_dbenv()
def resolve_entity(
    entity: orm.Entity, info: gr.ResolveInfo, pk: int
) -> ENTITY_DICT_TYPE:
    """Query for a single entity, and project only the fields requested."""
    project = get_projection(info)
    entities = (
        orm.QueryBuilder()
        .append(entity, tag="result", filters={"id": pk}, project=project)
        .dict()
    )
    if not entities:
        return None
    return entities[0]["result"]


class Query(gr.ObjectType):

    User = gr.Field(UserEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_User(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.User, info, id)

    Users = gr.Field(UsersEntity)

    @staticmethod
    def resolve_Users(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to UsersEntity
        return {}

    Computer = gr.Field(ComputerEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Computer(
        parent: Any, info: gr.ResolveInfo, id: int
    ) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Computer, info, id)

    Computers = gr.Field(ComputersEntity)

    @staticmethod
    def resolve_Computers(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to ComputersEntity
        return {}

    Node = gr.Field(
        NodeEntity,
        id=gr.Int(required=True),
    )

    @staticmethod
    def resolve_Node(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.nodes.Node, info, id)

    Nodes = gr.Field(NodesEntity, **nodes_filter_kwargs)

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter to NodesEntity
        return {"filters": create_nodes_filter(kwargs)}

    Comment = gr.Field(CommentEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Comment(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Comment, info, id)

    Comments = gr.Field(CommentsEntity)

    @staticmethod
    def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to NodesEntity
        return {}

    Group = gr.Field(GroupEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Group(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Group, info, id)

    Groups = gr.Field(GroupsEntity)

    @staticmethod
    def resolve_Groups(parent: Any, info: gr.ResolveInfo) -> dict:
        # pass filter to GroupsEntity
        return {}


app = GraphQLApp(schema=gr.Schema(query=Query, auto_camelcase=False))
