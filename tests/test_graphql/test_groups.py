"""Tests for group plugins."""

from graphene.test import Client

from aiida_restapi.graphql.groups import GroupQueryPlugin, GroupsQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_group(create_group, orm_regression):
    """Test Group query."""
    group = create_group()
    fields = field_names_from_orm(type(group))
    schema = create_schema([GroupQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ group(id: %r) { %s } }' % (group.id, ' '.join(fields)))
    orm_regression(executed)


def test_group_label(create_group, orm_regression):
    """Test Group query on the label."""
    group = create_group(label='custom-label')
    fields = field_names_from_orm(type(group))
    schema = create_schema([GroupQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ group(label: "custom-label") { %s } }' % (' '.join(fields)))
    orm_regression(executed)


def test_group_nodes(create_group, create_node, orm_regression):
    """Test querying Nodes inside Group."""
    create_node(label='not in group')
    group = create_group()
    group.add_nodes([create_node(label='node 1'), create_node(label='node 2')])
    schema = create_schema([GroupQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ group(id: %r) { nodes { count rows{ label } } } }' % (group.id))
    orm_regression(executed)


def test_groups(create_group, orm_regression):
    """Test Groups query, for all fields."""
    create_group(label='group1')
    group = create_group(label='group2')
    fields = field_names_from_orm(type(group))
    schema = create_schema([GroupsQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ groups {  count rows { %s } } }' % ' '.join(fields))
    orm_regression(executed)
