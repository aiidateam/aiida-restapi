"""Pagination utilities."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import orm  # noqa: F401

from .types import EntityModelType

__all__ = ('PaginatedResults',)


class PaginatedResults(pdt.BaseModel, t.Generic[EntityModelType]):
    total: int
    page: int
    page_size: int
    results: list[EntityModelType]


PaginatedResults.model_rebuild()
