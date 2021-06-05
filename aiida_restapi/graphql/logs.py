# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

import graphene as gr
from aiida.orm import Log

from .orm_factories import multirow_cls_factory, single_cls_factory


class LogQuery(single_cls_factory(Log)):
    """An AiiDA Log"""


class LogsQuery(multirow_cls_factory(LogQuery, Log, "logs")):
    """All AiiDA Logs."""
