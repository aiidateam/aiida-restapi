# -*- coding: utf-8 -*-
"""Tests for basic plugins."""
from aiida import __version__
from graphene.test import Client

from aiida_restapi.graphql.entry_points import (
    aiidaEntryPointGroupsPlugin,
    aiidaEntryPointsPlugin,
)
from aiida_restapi.graphql.plugins import create_schema


def test_aiidaEntryPointGroups():
    """Test test_aiidaEntryPointGroups query."""
    schema = create_schema([aiidaEntryPointGroupsPlugin])
    client = Client(schema)
    executed = client.execute("{ aiidaEntryPointGroups }")
    assert "data" in executed, executed
    assert "aiidaEntryPointGroups" in executed["data"], executed["data"]
    assert "aiida.data" in executed["data"]["aiidaEntryPointGroups"], executed["data"]


def test_aiidaEntryPoints():
    """Test aiidaEntryPoints query."""
    schema = create_schema([aiidaEntryPointsPlugin])
    client = Client(schema)
    executed = client.execute(
        '{ aiidaEntryPoints(group: "aiida.schedulers") { group names } }'
    )
    assert "data" in executed, executed
    assert "aiidaEntryPoints" in executed["data"]
    assert executed["data"]["aiidaEntryPoints"]["group"] == "aiida.schedulers"
    assert "direct" in executed["data"]["aiidaEntryPoints"]["names"]
