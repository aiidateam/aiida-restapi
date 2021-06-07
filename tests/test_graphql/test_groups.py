# -*- coding: utf-8 -*-
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
    executed = client.execute("{ Group(id: %r) { %s } }" % (group.id, " ".join(fields)))
    orm_regression(executed)


def test_groups(create_group, orm_regression):
    """Test Groups query, for all fields."""
    create_group(label="group1")
    group = create_group(label="group2")
    fields = field_names_from_orm(type(group))
    schema = create_schema([GroupsQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Groups {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
