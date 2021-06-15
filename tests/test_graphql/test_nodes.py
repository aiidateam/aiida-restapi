# -*- coding: utf-8 -*-
"""Tests for node plugins."""
from aiida.common.links import LinkType
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
    executed = client.execute("{ node(id: %r) { %s } }" % (node.id, " ".join(fields)))
    orm_regression(executed)


def test_node_logs(create_node, create_log, orm_regression):
    """Test queryinglogs of a node."""
    node = create_node(label="mynode")
    create_log(message="log 1", node=node)
    create_log(message="log 2", node=node)
    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { logs { count rows{ message } } } }" % (node.id)
    )
    orm_regression(executed)


def test_node_comments(create_node, create_comment, orm_regression):
    """Test querying comments of a node."""
    node = create_node(label="mynode")
    create_comment(content="comment 1", node=node)
    create_comment(content="comment 2", node=node)
    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { comments { count rows{ content } } } }" % (node.id)
    )
    orm_regression(executed)


def test_node_incoming(create_node, orm_regression):
    """Test querying incoming links to a node."""
    node = create_node(label="mynode", process_type="process", store=False)
    for label, link_type, link_label in [
        ("incoming1", LinkType.INPUT_CALC, "link1"),
        ("incoming2", LinkType.INPUT_CALC, "link2"),
    ]:
        node.add_incoming(create_node(label=label), link_type, link_label)
    node.store()

    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { incoming { count rows{ node { label } link { label type } } } } }"
        % (node.id)
    )
    orm_regression(executed)


def test_node_outgoing(create_node, orm_regression):
    """Test querying ancestor links to a node."""
    node = create_node(label="mynode", process_type="process")
    for label, link_type, link_label in [
        ("outgoing1", LinkType.CREATE, "link1"),
        ("outgoing2", LinkType.CREATE, "link2"),
    ]:
        outgoing = create_node(label=label)
        outgoing.add_incoming(node, link_type, link_label)
        outgoing.store()

    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { outgoing { count rows{ node { label } link { label type } } } } }"
        % (node.id)
    )
    orm_regression(executed)


def test_node_ancestors(create_node, orm_regression):
    """Test querying incoming links to a node."""
    node = create_node(label="mynode", process_type="process", store=False)
    for label, link_type, link_label in [
        ("incoming1", LinkType.INPUT_CALC, "link1"),
        ("incoming2", LinkType.INPUT_CALC, "link2"),
    ]:
        node.add_incoming(create_node(label=label), link_type, link_label)
    node.store()

    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { ancestors { count rows{ label } } } }" % (node.id)
    )
    orm_regression(executed)


def test_node_descendants(create_node, orm_regression):
    """Test querying descendant links to a node."""
    node = create_node(label="mynode", process_type="process")
    for label, link_type, link_label in [
        ("outgoing1", LinkType.CREATE, "link1"),
        ("outgoing2", LinkType.CREATE, "link2"),
    ]:
        outgoing = create_node(label=label)
        outgoing.add_incoming(node, link_type, link_label)
        outgoing.store()

    schema = create_schema([NodeQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ node(id: %r) { descendants { count rows{ label } } } }" % (node.id)
    )
    orm_regression(executed)


def test_nodes(create_node, orm_regression):
    """Test Nodes query, for all fields."""
    create_node(label="node 1")
    node = create_node(label="node 2")
    fields = field_names_from_orm(type(node))
    schema = create_schema([NodesQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ nodes {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
