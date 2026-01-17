"""Pagination utilities."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida.orm import Entity

ResultType = t.TypeVar('ResultType', bound=Entity.Model)

__all__ = ('PaginatedResults',)


class PaginatedResults(pdt.BaseModel, t.Generic[ResultType]):
    total: int
    page: int
    page_size: int
    results: list[ResultType]
