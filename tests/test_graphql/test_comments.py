"""Tests for comments plugins."""

from graphene.test import Client

from aiida_restapi.graphql.comments import CommentQueryPlugin, CommentsQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_comment(create_comment, orm_regression):
    """Test Comment query, for all fields."""
    comment = create_comment()
    fields = field_names_from_orm(type(comment))
    schema = create_schema([CommentQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ comment(id: %r) { %s } }' % (comment.pk, ' '.join(fields)))
    orm_regression(executed)


def test_comments(create_comment, orm_regression):
    """Test Comments query, for all fields."""
    create_comment(content='comment 1')
    comment = create_comment(content='comment 2')
    fields = field_names_from_orm(type(comment))
    schema = create_schema([CommentsQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ comments {  count rows { %s } } }' % ' '.join(fields))
    orm_regression(executed)


def test_comments_order_by(create_comment, orm_regression):
    """Test Comments query, when ordering by a field."""
    create_comment(content='b')
    create_comment(content='a')
    create_comment(content='c')
    schema = create_schema([CommentsQueryPlugin])
    client = Client(schema)
    executed = client.execute('{ comments {  count rows(orderBy: "content", orderAsc: false) { content } } }')
    orm_regression(executed)
