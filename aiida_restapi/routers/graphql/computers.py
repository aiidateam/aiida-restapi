# -*- coding: utf-8 -*-
# pylint: disable=unused-argument

from typing import Any

import graphene as gr
from aiida.orm import Computer

from .nodes import NodesEntity
from .utils import JSON, make_entities_cls


class ComputerEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    name = gr.String(description="Computer name")
    hostname = gr.String(description="Computer name")
    description = gr.String(description="Computer name")
    scheduler_type = gr.String(description="Scheduler type")
    transport_type = gr.String(description="Transport type")
    metadata = JSON(description="Metadata of the computer")
    Nodes = gr.Field(NodesEntity, **NodesEntity.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesEntity
        filters = NodesEntity.create_nodes_filter(kwargs)
        filters["dbcomputer_id"] = parent["id"]
        return {"filters": filters}


class ComputersEntity(make_entities_cls(ComputerEntity, Computer, "computers")):
    """A list of computers"""
