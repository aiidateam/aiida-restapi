"""Common type variables."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.common.pydantic import OrmModel

EntityType = t.TypeVar('EntityType', bound='orm.Entity')
EntityModelType = t.TypeVar('EntityModelType', bound='OrmModel')

NodeType = t.TypeVar('NodeType', bound='orm.Node')
NodeModelType = t.TypeVar('NodeModelType', bound='orm.Node.BaseNodeModel')
