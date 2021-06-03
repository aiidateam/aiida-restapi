# -*- coding: utf-8 -*-
import graphene as gr
from aiida.orm import Comment

from .utils import make_entities_cls


class CommentEntity(gr.ObjectType):
    id = gr.Int(description="Unique user id (pk)")
    uuid = gr.ID(description="Unique uuid")
    ctime = gr.DateTime(description="Creation time")
    mtime = gr.DateTime(description="Last modification time")
    content = gr.String(description="Content of the comment")
    user_id = gr.Int(description="Created by user id (pk)")
    dbnode_id = gr.Int(description="Associated node id (pk)")


class CommentsEntity(make_entities_cls(CommentEntity, Comment, "comments")):
    """A list of comments."""
