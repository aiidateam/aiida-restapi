# -*- coding: utf-8 -*-
# pylint: disable=unused-argument

from typing import Any

import graphene as gr
from aiida.orm import Computer

from .nodes import NodesQuery
from .orm_factories import multirow_cls_factory, single_cls_factory
from .utils import JSON


class ComputerQuery(single_cls_factory(Computer)):
    """An AiiDA Computer"""

    Nodes = gr.Field(NodesQuery, **NodesQuery.get_filter_kwargs())

    @staticmethod
    def resolve_Nodes(parent: Any, info: gr.ResolveInfo, **kwargs) -> dict:
        # pass filter specification to NodesQuery
        filters = NodesQuery.create_nodes_filter(kwargs)
        filters["dbcomputer_id"] = parent["id"]
        return {"filters": filters}


class ComputersQuery(multirow_cls_factory(ComputerQuery, Computer, "computers")):
    """All AiiDA Computers"""
