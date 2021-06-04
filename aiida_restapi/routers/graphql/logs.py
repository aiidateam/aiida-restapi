# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

import graphene as gr
from aiida.orm import Log

from .utils import JSON, make_entities_cls


class LogEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    time = gr.DateTime(description="Creation time")
    loggername = gr.String(description="The loggers name")
    levelname = gr.String(description="The log level")
    message = gr.String(description="The log message")
    metadata = JSON(description="Metadata associated with the log")
    dbnode_id = gr.Int(description="Associated node id (pk)")


class LogsEntity(make_entities_cls(LogEntity, Log, "logs")):
    """A list of logs."""
