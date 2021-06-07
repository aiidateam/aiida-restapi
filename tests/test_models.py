# -*- coding: utf-8 -*-
"""Test that all aiida entity models can be loaded loaded into pydantic models."""
from aiida import orm

from aiida_restapi import models


def replace_dynamic(data: dict) -> dict:
    """Replace dynamic fields with their type name."""
    for key in ["id", "uuid", "dbnode_id", "user_id", "mtime", "ctime"]:
        if key in data:
            data[key] = type(data[key]).__name__
    return data


def test_comment_get_entities(data_regression):
    """Test ``Comment.get_entities``"""
    orm_user = orm.User(
        email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi"
    ).store()
    orm_node = orm.Data().store()
    orm.Comment(orm_node, orm_user, "content").store()
    py_comments = models.Comment.get_entities(order_by=["id"])
    data_regression.check([replace_dynamic(c.dict()) for c in py_comments])


def test_user_get_entities(data_regression):
    """Test ``User.get_entities``"""
    orm.User(email="verdi@opera.net", first_name="Giuseppe", last_name="Verdi").store()
    py_users = models.User.get_entities(order_by=["id"])
    data_regression.check([replace_dynamic(c.dict()) for c in py_users])


def test_group_get_entities(data_regression):
    """Test ``Group.get_entities``"""
    orm.Group(label="regression_label_1", description="regrerssion_test").store()
    py_group = models.Group.get_entities(order_by=["id"])
    data_regression.check([replace_dynamic(c.dict()) for c in py_group])
