"""Pagination utilities."""

from __future__ import annotations

import typing as t

import pydantic as pdt

ResultType = t.TypeVar('ResultType')

__all__ = [
    'PaginatedResults',
]


class PaginatedResults(pdt.BaseModel, t.Generic[ResultType]):
    total: int
    page: int
    page_size: int
    data: list[ResultType]
