"""Defines plugins for retrieving entry-point group and name lists."""

# pylint: disable=too-few-public-methods,unused-argument
from typing import Any, Dict, List

import graphene as gr
from aiida.plugins.entry_point import (
    ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP,
    get_entry_point_names,
)

from .plugins import QueryPlugin


class EntryPoints(gr.ObjectType):
    """Return type from an entry point group and its list of registered names."""

    group = gr.String()
    names = gr.List(gr.String)


def resolve_aiidaEntryPointGroups(parent: Any, info: gr.ResolveInfo) -> List[str]:
    """Resolution function."""
    return list(ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP.keys())


def resolve_aiidaEntryPoints(parent: Any, info: gr.ResolveInfo, group: str) -> Dict[str, Any]:
    """Resolution function."""
    return {'group': group, 'names': get_entry_point_names(group)}


aiidaEntryPointGroupsPlugin = QueryPlugin(
    'aiidaEntryPointGroups',
    gr.List(gr.String, description='List of the entrypoint group names'),
    resolve_aiidaEntryPointGroups,
)
aiidaEntryPointsPlugin = QueryPlugin(
    'aiidaEntryPoints',
    gr.Field(
        EntryPoints,
        description='List of the entrypoint names in a group',
        group=gr.String(required=True),
    ),
    resolve_aiidaEntryPoints,
)
