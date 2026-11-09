"""Common type variables."""

from __future__ import annotations

import typing as t
from uuid import UUID

from aiida import orm
from fastapi import Request
from fastapi import exceptions as fastapi_exceptions

from aiida_restapi.common.responses import JsonApiResponse

EntityType = t.TypeVar('EntityType', bound='orm.Entity')
EntityModelType = t.TypeVar('EntityModelType', bound='orm.OrmModel')

NodeType = t.TypeVar('NodeType', bound='orm.Node')
NodeModelType = t.TypeVar('NodeModelType', bound='orm.Node.BaseNodeModel')

EntityIdentifier: t.TypeAlias = int | UUID

RequestValidationErrorHandler = t.Callable[
    [
        Request,
        fastapi_exceptions.RequestValidationError,
    ],
    JsonApiResponse | None,
]
