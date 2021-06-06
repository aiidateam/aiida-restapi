# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA process node logs."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any

import graphene as gr
from aiida.orm import Log

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .plugins import QueryPlugin


class LogQuery(single_cls_factory(Log)):  # type: ignore[misc]
    """Query an AiiDA Log"""


class LogsQuery(multirow_cls_factory(LogQuery, Log, "logs")):  # type: ignore[misc]
    """Query all AiiDA Logs."""


def resolve_Log(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Log, info, id)


def resolve_Logs(parent: Any, info: gr.ResolveInfo) -> dict:
    """Resolution function."""
    # pass filter to LogsQuery
    return {}


LogQueryPlugin = QueryPlugin(
    "Log", gr.Field(LogQuery, id=gr.Int(required=True)), resolve_Log
)
LogsQueryPlugin = QueryPlugin("Logs", gr.Field(LogsQuery), resolve_Logs)
