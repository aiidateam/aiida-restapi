"""Simple test for the full schema."""

from graphene.test import Client

from aiida_restapi.graphql.main import SCHEMA


def test_full(create_node, orm_regression):
    """Test loading the full schema."""
    node = create_node(label='node 1')
    client = Client(SCHEMA)
    executed = client.execute('{ aiidaVersion node(id: %r) { label } }' % (node.id))
    orm_regression(executed)
