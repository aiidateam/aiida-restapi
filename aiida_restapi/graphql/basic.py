"""Defines plugins for basic information about aiida etc."""

# pylint: disable=too-few-public-methods,unused-argument
from typing import Any

import aiida
import graphene as gr

from aiida_restapi.graphql.config import ENTITY_LIMIT

from .plugins import QueryPlugin


def resolve_rowLimitMax(parent: Any, info: gr.ResolveInfo) -> int:
    """Get row maximum number of rows."""
    return ENTITY_LIMIT


def resolve_aiidaVersion(parent: Any, info: gr.ResolveInfo) -> str:
    """Get AiiDA version."""
    return aiida.__version__


rowLimitMaxPlugin = QueryPlugin(
    'rowLimitMax',
    gr.Int(description='Maximum number of entity rows allowed to be returned from a query'),
    resolve_rowLimitMax,
)

aiidaVersionPlugin = QueryPlugin(
    'aiidaVersion',
    gr.String(description='Version of aiida-core'),
    resolve_aiidaVersion,
)
