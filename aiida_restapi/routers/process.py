# -*- coding: utf-8 -*-
"""Declaration of FastAPI router for processes."""

from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from aiida.engine import submit
from aiida.orm.querybuilder import QueryBuilder
from aiida.plugins import load_entry_point_from_string
from fastapi import APIRouter, Depends, HTTPException

from aiida_restapi.models import Process, Process_Post, User

from .auth import get_current_active_user

router = APIRouter()


def substitute_node(input_dict: dict) -> dict:
    """Substitutes node ids with nodes"""
    node_ids = {
        key: node_id for key, node_id in input_dict.items() if not key.endswith(".uuid")
    }

    for key, value in input_dict.items():
        if key not in node_ids.keys():
            try:
                node_ids[key[:-5]] = orm.Node.get(uuid=value)
            except NotExistent as exc:
                raise HTTPException(
                    status_code=404,
                    detail="Node ID: {} does not exist.".format(value),
                ) from exc

    return node_ids


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


@router.post("/processes", response_model=Process)
@with_dbenv()
async def post_process(
    process: Process_Post,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> Optional[Process]:
    """Create new process."""
    process_dict = process.dict(exclude_unset=True, exclude_none=True)
    inputs = substitute_node(process_dict["inputs"])
    entry_point = process_dict.get("process_entry_point")

    try:
        entry_point_process = load_entry_point_from_string(entry_point)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Entry point '{}' not recognized.".format(entry_point),
        ) from exc

    process_node = submit(entry_point_process, **inputs)

    return process_node
