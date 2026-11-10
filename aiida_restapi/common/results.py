"""Generic result models shared by REST API services and adapters."""

from __future__ import annotations

import typing as t

import pydantic as pdt

ResultType = t.TypeVar('ResultType')


class PaginatedResults(pdt.BaseModel, t.Generic[ResultType]):
    """A page of results with total count and requested pagination window."""

    total: int
    offset: int
    limit: int
    data: list[ResultType]
