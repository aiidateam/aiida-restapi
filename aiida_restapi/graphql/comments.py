# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

import graphene as gr
from aiida.orm import Comment

from .orm_factories import multirow_cls_factory, single_cls_factory


class CommentQuery(single_cls_factory(Comment)):
    """An AiiDA Comment"""


class CommentsQuery(multirow_cls_factory(CommentQuery, Comment, "comments")):
    """All AiiDA Comments."""
