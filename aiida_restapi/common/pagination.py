"""Pagination utilities."""

from __future__ import annotations

import typing as t

import pydantic as pdt

from .types import EntityModelType


class PaginatedResults(pdt.BaseModel, t.Generic[EntityModelType]):
    total: int
    page: int
    page_size: int
    results: list[EntityModelType]
