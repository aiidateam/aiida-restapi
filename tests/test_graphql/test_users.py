# -*- coding: utf-8 -*-
"""Tests for user plugins."""
from graphene.test import Client

from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema
from aiida_restapi.graphql.users import UserQueryPlugin, UsersQueryPlugin


def test_user(create_user, orm_regression):
    """Test User query."""
    user = create_user()
    fields = field_names_from_orm(type(user))
    schema = create_schema([UserQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ User(id: %r) { %s } }" % (user.id, " ".join(fields)))
    orm_regression(executed)


def test_users(create_user, orm_regression):
    """Test Users query, for all fields."""
    create_user(email="a@b.com")
    user = create_user(email="c@d.com")
    fields = field_names_from_orm(type(user))
    schema = create_schema([UsersQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Users {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
