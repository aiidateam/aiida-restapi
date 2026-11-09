"""Declaration of FastAPI router for submission."""

from __future__ import annotations

import typing as t

from aiida import engine, orm
from aiida.common import exceptions
from aiida.manage import get_manager
from aiida.manage.configuration import profile_context
from aiida.orm.implementation import StorageBackend
from aiida.plugins.entry_point import load_entry_point_from_string
from fastapi import APIRouter, Depends, Request

from aiida_restapi.common.responses import JsonApiResponse
from aiida_restapi.jsonapi.adapters import JsonApiAdapter as JsonApi
from aiida_restapi.jsonapi.models import aiida, errors
from aiida_restapi.models.process import SubmittedProcess
from aiida_restapi.profiles import get_profile_backend

write_router = APIRouter(prefix='/submit')


def _process_inputs(inputs: dict[str, t.Any], backend: StorageBackend) -> dict[str, t.Any]:
    """Resolve nested ``*.uuid`` input references to stored AiiDA nodes."""
    uuid_suffix = '.uuid'
    resolved = {}

    for key, value in inputs.items():
        if isinstance(value, dict):
            resolved[key] = _process_inputs(value, backend)
        elif key.endswith(uuid_suffix):
            resolved[key[: -len(uuid_suffix)]] = orm.Node.get_collection(backend).get(uuid=value)
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
async def submit_process(
    request: Request,
    process: SubmittedProcess,
    backend: t.Annotated[StorageBackend, Depends(get_profile_backend)],
) -> dict[str, t.Any]:
    """Submit new AiiDA process."""
    try:
        entry_point_process = load_entry_point_from_string(process.entry_point)
    except Exception as exception:
        raise exceptions.EntryPointError(str(exception)) from exception

    with profile_context(backend.profile, allow_switch=True):
        manager = get_manager()
        submit_backend = manager.get_profile_storage()
        inputs = _process_inputs(process.inputs, submit_backend)

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
        backend=backend,
    )
