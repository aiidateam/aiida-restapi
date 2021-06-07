# -*- coding: utf-8 -*-
"""Tests for node plugins."""
from graphene.test import Client

from aiida_restapi.graphql.nodes import NodeQueryPlugin, NodesQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_node(create_node, orm_regression):
    """Test Node query."""
    node = create_node(process_type="my_process")
    fields = field_names_from_orm(type(node))
    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Node(id: %r) { %s } }" % (node.id, " ".join(fields)))
    orm_regression(executed)


def test_node_logs(create_node, create_log, orm_regression):
    """Test querying Nodes inside Computer."""
    node = create_node(label="mynode")
    create_log(message="log 1", node=node)
    create_log(message="log 2", node=node)
    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ Node(id: %r) { Logs { count rows{ message } } } }" % (node.id)
    )
    orm_regression(executed)


def test_node_comments(create_node, create_comment, orm_regression):
    """Test querying Nodes inside Computer."""
    node = create_node(label="mynode")
    create_comment(content="comment 1", node=node)
    create_comment(content="comment 2", node=node)
    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ Node(id: %r) { Comments { count rows{ content } } } }" % (node.id)
    )
    orm_regression(executed)


def test_nodes(create_node, orm_regression):
    """Test Nodes query, for all fields."""
    create_node(label="node 1")
    node = create_node(label="node 2")
    fields = field_names_from_orm(type(node))
    schema = create_schema([NodesQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Nodes {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
