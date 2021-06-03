# -*- coding: utf-8 -*-
# pylint: disable=redefined-builtin,unused-argument,too-few-public-methods,missing-function-docstring
from typing import Any, Dict, List, Optional

import graphene as gr
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from graphene.types.generic import GenericScalar
from starlette.graphql import GraphQLApp

from .nodes import NodeEntity, NodesEntity, create_nodes_filter, nodes_filter_kwargs
from .utils import get_projection

ENTITY_DICT_TYPE = Optional[Dict[str, Any]]


@with_dbenv()
def resolve_entity(
    entity: orm.Entity, info: gr.ResolveInfo, pk: int, joined: List[str] = ()
) -> ENTITY_DICT_TYPE:
    """Query for a single entity, and project only the fields requested."""
    project = get_projection(info, joined)
    entities = (
        orm.QueryBuilder()
        .append(entity, tag="result", filters={"id": pk}, project=project)
        .dict()
    )
    if not entities:
        return None
    return entities[0]["result"]


class UserEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)", required=True)
    email = gr.ID(description="Email address of the user")
    first_name = gr.String(description="First name of the user")
    last_name = gr.String(description="Last name of the user")
    institution = gr.String(description="Host institution or workplace of the user")
    nodes = gr.Field(NodesEntity, **nodes_filter_kwargs)

    @staticmethod
    def resolve_nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesEntity
        filters = create_nodes_filter(kwargs)
        filters["user_id"] = parent["id"]
        return {"filters": filters}


class ComputerEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    name = gr.String(description="Computer name")
    hostname = gr.String(description="Computer name")
    description = gr.String(description="Computer name")
    scheduler_type = gr.String(description="Scheduler type")
    transport_type = gr.String(description="Transport type")
    metadata = GenericScalar(description="Metadata of the computer")
    nodes = gr.Field(NodesEntity, **nodes_filter_kwargs)

    @staticmethod
    def resolve_nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesEntity
        filters = create_nodes_filter(kwargs)
        filters["dbcomputer_id"] = parent["id"]
        return {"filters": filters}


class CommentEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    ctime = gr.DateTime(description="Creation time")
    mtime = gr.DateTime(description="Last modification time")
    content = gr.String(description="Content of the comment")
    user_id = gr.Int(description="Created by user id (pk)")
    dbnode_id = gr.Int(description="Associated node id (pk)")


class GroupEntity(gr.ObjectType):
    id = gr.Int(description="Unique id (pk)")
    uuid = gr.ID(description="Unique uuid")
    label = gr.String(description="Label of group")
    type_string = gr.String(description="type of the group")
    time = gr.DateTime(description="Created time")
    description = gr.String(description="Description of group")
    extras = GenericScalar(description="extra data about for the group")
    user_id = gr.Int(description="Created by user id (pk)")


class Query(gr.ObjectType):

    User = gr.Field(UserEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_User(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.User, info, id, ["nodes"])

    Computer = gr.Field(ComputerEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Computer(
        parent: Any, info: gr.ResolveInfo, id: int
    ) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Computer, info, id, ["nodes"])

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

    Group = gr.Field(GroupEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Group(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
        return resolve_entity(orm.Group, info, id)


app = GraphQLApp(schema=gr.Schema(query=Query, auto_camelcase=False))
