# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA groups."""
# pylint: disable=too-few-public-methods,redefined-builtin,,unused-argument

from typing import Any, Optional, Tuple

import graphene as gr
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm import Group

from aiida_restapi.filter_syntax import parse_filter_str
from aiida_restapi.graphql.nodes import NodesQuery
from aiida_restapi.graphql.plugins import MutationPlugin, QueryPlugin

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .utils import FilterString


class GroupQuery(single_cls_factory(Group)):  # type: ignore[misc]
    """Query an AiiDA Group"""

    nodes = gr.Field(NodesQuery)

    @staticmethod
    def resolve_nodes(parent: Any, info: gr.ResolveInfo) -> dict:
        """Resolution function."""
        # pass group specification to NodesQuery
        return {"group_id": parent["id"]}


class GroupsQuery(multirow_cls_factory(GroupQuery, Group, "groups")):  # type: ignore[misc]
    """Query all AiiDA Groups"""


def resolve_Group(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
    label: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Group, info, id, uuid, label)


def resolve_Groups(
    parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None
) -> dict:
    """Resolution function."""
    # pass filter to GroupsQuery
    return {"filters": parse_filter_str(filters)}


GroupQueryPlugin = QueryPlugin(
    "group",
    gr.Field(
        GroupQuery,
        id=gr.Int(),
        uuid=gr.String(),
        label=gr.String(),
        description="Query for a single Group",
    ),
    resolve_Group,
)
GroupsQueryPlugin = QueryPlugin(
    "groups",
    gr.Field(
        GroupsQuery,
        description="Query for multiple Groups",
        filters=FilterString(),
    ),
    resolve_Groups,
)


class GroupCreate(gr.Mutation):
    """Create an AiiDA group (or change an existing one)."""

    class Arguments:
        """The arguments to create a group."""

        label = gr.String(required=True)
        description = gr.String(default_value="")
        type_string = gr.String()

    created = gr.Boolean(
        description="Whether the group was created or already existed."
    )
    group = gr.Field(lambda: GroupQuery)

    @with_dbenv()
    @staticmethod
    def mutate(
        root: Any,
        info: gr.ResolveInfo,
        label: str,
        description: str = "",
        type_string: Optional[str] = None,
    ) -> "GroupCreate":
        """Create the group and return the requested fields."""
        output: Tuple[Group, bool] = Group.objects.get_or_create(
            label=label, description=description, type_string=type_string
        )
        orm_group, created = output
        if not created and not orm_group.description == description:
            orm_group.description = description
        group = GroupQuery(
            id=orm_group.id,
            uuid=orm_group.uuid,
            label=orm_group.label,
            type_string=orm_group.type_string,
            description=orm_group.description,
        )
        return GroupCreate(group=group, created=created)


GroupCreatePlugin = MutationPlugin("groupCreate", GroupCreate)
