# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA groups."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any

import graphene as gr
from aiida.orm import Group

from aiida_restapi.graphql.plugins import QueryPlugin

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)


class GroupQuery(single_cls_factory(Group)):  # type: ignore[misc]
    """Query an AiiDA Group"""


class GroupsQuery(multirow_cls_factory(GroupQuery, Group, "groups")):  # type: ignore[misc]
    """Query all AiiDA Groups"""


def resolve_Group(parent: Any, info: gr.ResolveInfo, id: int) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Group, info, id)


def resolve_Groups(parent: Any, info: gr.ResolveInfo) -> dict:
    """Resolution function."""
    # pass filter to GroupsQuery
    return {}


GroupQueryPlugin = QueryPlugin(
    "Group", gr.Field(GroupQuery, id=gr.Int(required=True)), resolve_Group
)
GroupsQueryPlugin = QueryPlugin("Groups", gr.Field(GroupsQuery), resolve_Groups)
