"""Tests for basic plugins."""

from aiida import __version__
from graphene.test import Client

from aiida_restapi.graphql.basic import aiidaVersionPlugin, rowLimitMaxPlugin
from aiida_restapi.graphql.config import ENTITY_LIMIT
from aiida_restapi.graphql.plugins import create_schema


def test_aiidaVersion():
    """Test aiidaVersion query."""
    schema = create_schema([aiidaVersionPlugin])
    client = Client(schema)
    executed = client.execute('{ aiidaVersion }')
    assert 'aiidaVersion' in executed['data']
    assert executed['data']['aiidaVersion'] == __version__


def test_rowLimitMax():
    """Test rowLimitMax query."""
    schema = create_schema([rowLimitMaxPlugin])
    client = Client(schema)
    executed = client.execute('{ rowLimitMax }')
    assert 'rowLimitMax' in executed['data']
    assert executed['data']['rowLimitMax'] == ENTITY_LIMIT
