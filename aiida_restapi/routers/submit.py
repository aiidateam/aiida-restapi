"""Declaration of FastAPI router for processes."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import engine, orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from aiida.plugins.entry_point import load_entry_point_from_string
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_active_user

router = APIRouter()


def process_inputs(inputs: dict) -> dict:
    """Process the inputs dictionary converting each node UUID into the corresponding node by loading it.

    A node UUID is indicated by the key ending with the suffix ``.uuid``.

    :param inputs: The inputs dictionary.
    :returns: The deserialized inputs dictionary.
    :raises HTTPException: If the inputs contain a UUID that does not correspond to an existing node.
    """
    uuid_suffix = '.uuid'
    results = {}

    for key, value in inputs.items():
        if isinstance(value, dict):
            results[key] = process_inputs(value)
        elif key.endswith(uuid_suffix):
            try:
                results[key[: -len(uuid_suffix)]] = orm.load_node(uuid=value)
            except NotExistent as exc:
                raise HTTPException(
                    status_code=404,
                    detail=f'Node with UUID `{value}` does not exist.',
                ) from exc
        else:
            results[key] = value

    return results


class ProcessSubmitModel(orm.ProcessNode.Model):
    entry_point: str = pdt.Field(..., description='The entry point of the process.')
    inputs: dict = pdt.Field(..., description='The inputs of the process.')


@router.post(
    '/submit',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
)
@with_dbenv()
async def submit_process(
    process: ProcessSubmitModel,
    current_user: t.Annotated[orm.User.Model, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Create new process."""
    process_dict = process.model_dump(exclude_unset=True, exclude_none=True)
    inputs = process_inputs(process_dict['inputs'])

    try:
        entry_point_process = load_entry_point_from_string(process.entry_point)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Entry point '{process.entry_point}' not recognized.",
        ) from exc

    process_node = engine.submit(entry_point_process, **inputs)
    return process_node.to_model()
