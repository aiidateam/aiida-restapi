# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""

from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter

from aiida_restapi.models import Process

router = APIRouter()


@router.get("/processes", response_model=List[Process])
@with_dbenv()
async def read_processes() -> List[Process]:
    """Get list of all processes"""

    return Process.get_entities()


@router.get("/processes/projectable_properties", response_model=List[str])
async def get_processes_projectable_properties() -> List[str]:
    """Get projectable properties for processes endpoint"""

    return Process.get_projectable_properties()


@router.get("/processes/{proc_id}", response_model=Process)
@with_dbenv()
async def read_process(proc_id: int) -> Optional[Process]:
    """Get process by id."""
    qbobj = QueryBuilder()
    qbobj.append(
        orm.ProcessNode, filters={"id": proc_id}, project=["**"], tag="process"
    ).limit(1)

    return qbobj.dict()[0]["process"]
