# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

import graphene as gr
from aiida.orm import Group

from .orm_factories import multirow_cls_factory, single_cls_factory
from .utils import JSON


class GroupQuery(single_cls_factory(Group)):
    """An AiiDA Group"""


class GroupsQuery(multirow_cls_factory(GroupQuery, Group, "groups")):
    """All AiiDA Groups"""
