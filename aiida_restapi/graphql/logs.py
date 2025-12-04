"""Defines plugins for AiiDA process node logs."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any, Optional

import graphene as gr
from aiida.orm import Log

from aiida_restapi.graphql.filter_syntax import parse_filter_str

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .plugins import QueryPlugin
from .utils import FilterString


class LogQuery(single_cls_factory(Log)):  # type: ignore[misc]
    """Query an AiiDA Log"""


class LogsQuery(multirow_cls_factory(LogQuery, Log, 'logs')):  # type: ignore[misc]
    """Query all AiiDA Logs."""


def resolve_Log(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Log, info, id, uuid)


def resolve_Logs(parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None) -> dict:
    """Resolution function."""
    # pass filter to LogsQuery
    return {'filters': parse_filter_str(filters)}


LogQueryPlugin = QueryPlugin(
    'log',
    gr.Field(LogQuery, id=gr.Int(), uuid=gr.String(), description='Query for a single Log'),
    resolve_Log,
)
LogsQueryPlugin = QueryPlugin(
    'logs',
    gr.Field(
        LogsQuery,
        description='Query for multiple Logs',
        filters=FilterString(),
    ),
    resolve_Logs,
)
