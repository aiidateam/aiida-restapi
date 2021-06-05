# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter, Depends

from aiida_restapi.models import Computer, User

from .auth import get_current_active_user

router = APIRouter()


@router.get("/computers", response_model=List[Computer])
@with_dbenv()
async def read_computers() -> List[Computer]:
    """Get list of all computers"""
    qbobj = QueryBuilder().append(orm.Computer, project=["**"])

    return [comp["computer_1"] for comp in qbobj.dict()]


@router.get("/computers/projectable_properties", response_model=List[str])
async def get_computers_projectable_properties() -> List[str]:
    """Get projectable properties for computers endpoint"""

    return Computer.get_projectable_properties()


@router.get("/computers/{comp_id}", response_model=Computer)
@with_dbenv()
async def read_computer(comp_id: int) -> Optional[Computer]:
    """Get computer by id."""
    qbobj = QueryBuilder()
    qbobj.append(orm.Computer, filters={"id": comp_id}, project=["**"]).limit(1)

    return qbobj.dict()[0]["computer_1"]


@router.post("/computers", response_model=Computer)
@with_dbenv()
async def create_computer(
    computer: Computer,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> Computer:
    """Create new AiiDA computer."""
    orm_computer = orm.Computer(**computer.dict(exclude_unset=True)).store()

    return Computer.from_orm(orm_computer)
