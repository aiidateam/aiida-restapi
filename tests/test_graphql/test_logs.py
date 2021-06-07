# -*- coding: utf-8 -*-
"""Tests for log plugins."""
from graphene.test import Client

from aiida_restapi.graphql.logs import LogQueryPlugin, LogsQueryPlugin
from aiida_restapi.graphql.orm_factories import field_names_from_orm
from aiida_restapi.graphql.plugins import create_schema


def test_log(create_log, orm_regression):
    """Test Log query."""
    log = create_log()
    fields = field_names_from_orm(type(log))
    schema = create_schema([LogQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Log(id: %r) { %s } }" % (log.id, " ".join(fields)))
    orm_regression(executed)


def test_logs(create_log, orm_regression):
    """Test Logs query, for all fields."""
    create_log(message="log 1")
    log = create_log(message="log 2")
    fields = field_names_from_orm(type(log))
    schema = create_schema([LogsQueryPlugin])
    client = Client(schema)
    executed = client.execute("{ Logs {  count rows { %s } } }" % " ".join(fields))
    orm_regression(executed)
