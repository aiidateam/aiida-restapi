"""Declaration of FastAPI router for submission."""

from __future__ import annotations

import typing as t

from aiida import engine, orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import exceptions
from aiida.plugins.entry_point import load_entry_point_from_string
from fastapi import APIRouter, Request

from aiida_restapi.common.responses import JsonApiResponse
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import aiida, errors
from aiida_restapi.models.process import SubmittedProcess

write_router = APIRouter(prefix='/submit')


def _process_inputs(inputs: dict[str, t.Any]) -> dict[str, t.Any]:
    """Resolve nested ``*.uuid`` input references to stored AiiDA nodes."""
    uuid_suffix = '.uuid'
    resolved = {}

    for key, value in inputs.items():
        if isinstance(value, dict):
            resolved[key] = _process_inputs(value)
        elif key.endswith(uuid_suffix):
            resolved[key[: -len(uuid_suffix)]] = orm.load_node(uuid=value)
        else:
            resolved[key] = value

    return resolved


@write_router.post(
    '',
    response_class=JsonApiResponse,
    response_model=aiida.NodeResourceDocument,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError},
        422: {'model': t.Union[errors.InvalidInputError, errors.InvalidOperationError]},
    },
)
@with_dbenv()
async def submit_process(
    request: Request,
    process: SubmittedProcess,
) -> dict[str, t.Any]:
    """Submit new AiiDA process."""
    try:
        entry_point_process = load_entry_point_from_string(process.entry_point)
    except Exception as exception:
        raise exceptions.EntryPointError(str(exception)) from exception
    inputs = _process_inputs(process.inputs)
    try:
        process_node = engine.submit(entry_point_process, **inputs)
    except Exception as exception:
        raise exceptions.InputValidationError(str(exception)) from exception
    serialized = process_node.serialize(minimal=True)
    return JsonApi.resource(
        request,
        serialized,
        resource_identity='uuid',
        resource_type='nodes',
    )
