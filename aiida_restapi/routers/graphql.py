from typing import Iterator, List, Optional
from graphql.language import ast
import graphene as gr
from graphene.types.generic import GenericScalar
from fastapi import FastAPI
from starlette.graphql import GraphQLApp
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv


def selected_field_names_naive(selection_set: ast.SelectionSet) -> Iterator[str]:
    """Get the list of field names that are selected at the current level.
    Does not include nested names.

    Taken from: https://github.com/graphql-python/graphene/issues/57#issuecomment-774227086
    """
    assert isinstance(selection_set, ast.SelectionSet)

    for node in selection_set.selections:
        # Field
        if isinstance(node, ast.Field):
            yield node.name.value
        # Fragment spread (`... fragmentName`)
        elif isinstance(node, (ast.FragmentSpread, ast.InlineFragment)):
            raise NotImplementedError(
                "Fragments are not supported by this simplistic function"
            )
        else:
            raise NotImplementedError(str(type(node)))


def get_projection(info: gr.ResolveInfo, joined: List[str] = ()) -> List[str]:
    try:
        fields = set(selected_field_names_naive(info.field_asts[0].selection_set))
        fields.difference_update(joined)
        if joined:
            fields.add("id")
        return list(fields)
    except NotImplementedError:
        return ["**"]


@with_dbenv()
def resolve_entity(
    entity: orm.Entity, info: gr.ResolveInfo, pk: int, skip: List[str] = ()
):
    project = get_projection(info, skip)
    entities = (
        orm.QueryBuilder()
        .append(entity, tag="result", filters={"id": pk}, project=project)
        .dict()
    )
    if not entities:
        return None
    return entities[0]["result"]


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
        filter=gr.List(gr.String, description="filter attributes keys"),
    )
    extras = GenericScalar(
        description="Variable extras (unsealed) of the node",
        filter=gr.List(gr.String, description="filter extras keys"),
    )

    @staticmethod
    def resolve_attributes(
        parent, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ):
        if filter is None:
            return parent.get("attributes")
        return {
            key: val
            for key, val in parent.get("attributes", {}).items()
            if key in filter
        }

    @staticmethod
    def resolve_extras(
        parent, info: gr.ResolveInfo, filter: Optional[List[str]] = None
    ):
        if filter is None:
            return parent.get("extras")
        return {
            key: val for key, val in parent.get("extras", {}).items() if key in filter
        }


class NodesEntity(gr.ObjectType):
    count = gr.Int(description="Total number of nodes")
    rows = gr.List(
        NodeEntity,
        limit=gr.Int(default_value=100, description="Maximum number of rows to return"),
        offset=gr.Int(default_value=0, description="Skip the first n rows"),
    )

    @with_dbenv()
    @staticmethod
    def resolve_count(parent, info: gr.ResolveInfo):
        query = orm.QueryBuilder().append(orm.Node, filters=parent.get("filters"))
        return query.count()

    @with_dbenv()
    @staticmethod
    def resolve_rows(parent, info: gr.ResolveInfo, limit: int, offset: int):
        project = get_projection(info)
        query = orm.QueryBuilder().append(
            orm.Node, tag="fields", filters=parent.get("filters"), project=project
        )
        query.offset(offset)
        query.limit(limit)
        return [d["fields"] for d in query.dict()]


class UserEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)", required=True)
    email = gr.ID(description="Email address of the user")
    first_name = gr.String(description="First name of the user")
    last_name = gr.String(description="Last name of the user")
    institution = gr.String(description="Host institution or workplace of the user")
    nodes = gr.Field(NodesEntity)

    @staticmethod
    def resolve_nodes(parent, info: gr.ResolveInfo):
        return {"filters": {"user_id": parent["id"]}}


class ComputerEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    name = gr.String(description="Computer name")
    hostname = gr.String(description="Computer name")
    description = gr.String(description="Computer name")
    scheduler_type = gr.String(description="Scheduler type")
    transport_type = gr.String(description="Transport type")
    metadata = GenericScalar(description="Metadata of the computer")
    nodes = gr.Field(NodesEntity)

    @staticmethod
    def resolve_nodes(parent, info: gr.ResolveInfo):
        return {"filters": {"dbcomputer_id": parent["id"]}}


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

    def resolve_User(parent, info: gr.ResolveInfo, id: int):
        return resolve_entity(orm.User, info, id, ["nodes"])

    Computer = gr.Field(ComputerEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Computer(parent, info: gr.ResolveInfo, id: int):
        return resolve_entity(orm.Computer, info, id, ["nodes"])

    Node = gr.Field(
        NodeEntity,
        id=gr.Int(required=True),
    )

    @staticmethod
    def resolve_Node(parent, info: gr.ResolveInfo, id: int):
        return resolve_entity(orm.nodes.Node, info, id)

    Nodes = gr.Field(NodesEntity)

    @staticmethod
    def resolve_Nodes(parent, info: gr.ResolveInfo):
        return {}

    Comment = gr.Field(CommentEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Comment(parent, info: gr.ResolveInfo, id: int):
        return resolve_entity(orm.Comment, info, id)

    Group = gr.Field(GroupEntity, id=gr.Int(required=True))

    @staticmethod
    def resolve_Group(parent, info: gr.ResolveInfo, id: int):
        return resolve_entity(orm.Group, info, id)


app = GraphQLApp(schema=gr.Schema(query=Query, auto_camelcase=False))
