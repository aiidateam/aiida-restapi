# -*- coding: utf-8 -*-
"""Tests for computer plugins."""
from graphene.test import Client

from aiida_restapi.graphql.computers import ComputerQueryPlugin
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
