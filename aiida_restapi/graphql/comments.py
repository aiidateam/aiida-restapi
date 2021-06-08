# -*- coding: utf-8 -*-
"""Defines plugins for AiiDA comments."""
# pylint: disable=too-few-public-methods,redefined-builtin,unused-argument

from typing import Any, Optional

import graphene as gr
from aiida.orm import Comment

from .orm_factories import (
    ENTITY_DICT_TYPE,
    multirow_cls_factory,
    resolve_entity,
    single_cls_factory,
)
from .plugins import QueryPlugin


class CommentQuery(single_cls_factory(Comment)):  # type: ignore[misc]
    """Query an AiiDA Comment"""


class CommentsQuery(multirow_cls_factory(CommentQuery, Comment, "comments")):  # type: ignore[misc]
    """Query all AiiDA Comments."""

    Comment = gr.Field(CommentQuery, id=gr.Int(), uuid=gr.String())


def resolve_Comment(
    parent: Any,
    info: gr.ResolveInfo,
    id: Optional[int] = None,
    uuid: Optional[str] = None,
) -> ENTITY_DICT_TYPE:
    """Resolution function."""
    return resolve_entity(Comment, info, id, uuid)


def resolve_Comments(parent: Any, info: gr.ResolveInfo) -> dict:
    """Resolution function."""
    # pass filter to CommentsQuery
    return {}


CommentQueryPlugin = QueryPlugin(
    "Comment",
    gr.Field(
        CommentQuery,
        id=gr.Int(),
        uuid=gr.String(),
        description="Query for a single Comment",
    ),
    resolve_Comment,
)
CommentsQueryPlugin = QueryPlugin(
    "Comments",
    gr.Field(CommentsQuery, description="Query for multiple Comments"),
    resolve_Comments,
)
