# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

import graphene as gr
from aiida.orm import Group

from .utils import JSON, make_entities_cls


class GroupEntity(gr.ObjectType):
    id = gr.Int(description="Unique id (pk)")
    uuid = gr.ID(description="Unique uuid")
    label = gr.String(description="Label of group")
    type_string = gr.String(description="type of the group")
    time = gr.DateTime(description="Created time")
    description = gr.String(description="Description of group")
    extras = JSON(description="extra data about for the group")
    user_id = gr.Int(description="Created by user id (pk)")


class GroupsEntity(make_entities_cls(GroupEntity, Group, "groups")):
    """A list of groups"""
