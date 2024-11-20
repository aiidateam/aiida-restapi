"""Defines plugins for AiiDA comments."""
# pylint: disable=too-few-public-methods,redefined-builtin,unused-argument

from typing import Any, Optional

import graphene as gr
from aiida.orm import Comment

from aiida_restapi.filter_syntax import parse_filter_str

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .plugins import QueryPlugin
from .utils import FilterString


class CommentQuery(single_cls_factory(Comment)):  # type: ignore[misc]
    """Query an AiiDA Comment"""


class CommentsQuery(multirow_cls_factory(CommentQuery, Comment, 'comments')):  # type: ignore[misc]
    """Query all AiiDA Comments."""


def resolve_Comment(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Comment, info, id, uuid)


def resolve_Comments(parent: Any, info: gr.ResolveInfo, filters: Optional[str] = None) -> dict:
    """Resolution function."""
    # pass filter to CommentsQuery
    return {'filters': parse_filter_str(filters)}


CommentQueryPlugin = QueryPlugin(
    'comment',
    gr.Field(
        CommentQuery,
        id=gr.Int(),
        uuid=gr.String(),
        description='Query for a single Comment',
    ),
    resolve_Comment,
)
CommentsQueryPlugin = QueryPlugin(
    'comments',
    gr.Field(CommentsQuery, description='Query for multiple Comments', filters=FilterString()),
    resolve_Comments,
)
