"""Declaration of FastAPI application."""

from __future__ import annotations

import typing as t

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.common import EntityRepository, PaginatedResults, QueryParams, query_params

from .auth import get_current_active_user

router = APIRouter()


repository = EntityRepository[orm.Computer, orm.Computer.Model](orm.Computer)


@router.get('/computers/projectable_properties', response_model=list[str])
async def get_computer_projectable_properties() -> list[str]:
    """Get projectable properties for AiiDA computers."""
    return repository.get_projectable_properties()


@router.get(
    '/computers',
    response_model=PaginatedResults[orm.Computer.Model],
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_computers(
    queries: t.Annotated[QueryParams, Depends(query_params)],
) -> PaginatedResults[orm.Computer.Model]:
    """Get AiiDA computers with optional filtering, sorting, and/or pagination."""
    return repository.get_entities(queries)


@router.get(
    '/computers/{comp_id}',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def get_computer(comp_id: int) -> orm.Computer.Model:
    """Get AiiDA computer by id."""
    return repository.get_entity_by_id(comp_id)


@router.post(
    '/computers',
    response_model=orm.Computer.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def create_computer(
    computer: orm.Computer.Model,
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Computer.Model:
    """Create new AiiDA computer."""
    return repository.create_entity(computer)
