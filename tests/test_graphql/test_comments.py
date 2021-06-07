# -*- coding: utf-8 -*-
"""Tests for comments plugins."""
from graphene.test import Client

from aiida_restapi.graphql.comments import CommentQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_comment(create_comment, orm_regression):
    """Test Comment query."""
    comment = create_comment()
    fields = field_names_from_orm(type(comment))
    schema = create_schema([CommentQueryPlugin])
    client = Client(schema)
    executed = client.execute(
        "{ Comment(id: %r) { %s } }" % (comment.id, " ".join(fields))
    )
    orm_regression(executed)
