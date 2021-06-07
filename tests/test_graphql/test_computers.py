# -*- coding: utf-8 -*-
"""Tests for computer plugins."""
from graphene.test import Client

from aiida_restapi.graphql.computers import ComputerQueryPlugin, ComputersQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_computer(create_computer, orm_regression):
    """Test Computer query."""
    computer = create_computer()
    fields = field_names_from_orm(type(computer))
    schema = create_schema([ComputerQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ Computer(id: %r) { %s } }" % (computer.id, " ".join(fields))
    )
    orm_regression(executed)


def test_computer_nodes(create_computer, create_node, orm_regression):
    """Test querying Nodes inside Computer."""
    computer = create_computer(label="mycomputer")
    create_node(label="node 1", computer=computer)
    create_node(label="node 2", computer=computer)
    schema = create_schema([ComputerQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ Computer(id: %r) { Nodes { count rows{ label } } } }" % (computer.id)
    )
    orm_regression(executed)


def test_computers(create_computer, orm_regression):
    """Test Computers query, for all fields."""
    create_computer(label="computer 1")
    computer = create_computer(label="computer 2")
    fields = field_names_from_orm(type(computer))
    schema = create_schema([ComputersQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Computers {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
