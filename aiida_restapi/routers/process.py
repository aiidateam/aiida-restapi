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


def process_inputs(inputs: dict) -> dict:
    """Process the inputs dictionary converting each node UUID into the corresponding node by loading it.

    A node UUID is indicated by the key ending with the suffix ``.uuid``.

    :param inputs: The inputs dictionary.
    :returns: The deserialized inputs dictionary.
    :raises HTTPException: If the inputs contain a UUID that does not correspond to an existing node.
    """
    uuid_suffix = ".uuid"
    results = {}

    for key, value in inputs.items():
        if isinstance(value, dict):
            results[key] = process_inputs(value)
        else:
            if key.endswith(uuid_suffix):
                try:
                    results[key[: -len(uuid_suffix)]] = orm.load_node(uuid=value)
                except NotExistent as exc:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Node with UUID `{value}` does not exist.",
                    ) from exc
            else:
                results[key] = value

    return results


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
        orm.ProcessNode, filters={"id": proc_id}, project="**", tag="process"
    ).limit(1)

    return qbobj.dict()[0]["process"]


@router.post("/processes", response_model=Process)
@with_dbenv()
async def post_process(
    process: Process_Post,
    current_user: User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> Optional[Process]:
    """Create new process."""
    process_dict = process.dict(exclude_unset=True, exclude_none=True)
    inputs = process_inputs(process_dict["inputs"])
    entry_point = process_dict.get("process_entry_point")

    try:
        entry_point_process = load_entry_point_from_string(entry_point)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Entry point '{entry_point}' not recognized.",
        ) from exc

    process_node = submit(entry_point_process, **inputs)

    return process_node
