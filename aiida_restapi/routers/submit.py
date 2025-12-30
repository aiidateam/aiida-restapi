"""Declaration of FastAPI router for submission."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import engine, orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common import exceptions
from aiida.plugins.entry_point import load_entry_point_from_string
from fastapi import APIRouter, Depends

from aiida_restapi.jsonapi.models import errors

from .auth import UserInDB, get_current_active_user

write_router = APIRouter(prefix='/submit')


def process_inputs(inputs: dict[str, t.Any]) -> dict[str, t.Any]:
    """Process the inputs dictionary converting each node UUID into the corresponding node by loading it.

    A node UUID is indicated by the key ending with the suffix ``.uuid``.

    :param inputs: The inputs dictionary.
    :type inputs: dict[str, t.Any]
    :returns: The deserialized inputs dictionary.
    :rtype: dict[str, t.Any]
    """
    uuid_suffix = '.uuid'
    results = {}

    for key, value in inputs.items():
        if isinstance(value, dict):
            results[key] = process_inputs(value)
        elif key.endswith(uuid_suffix):
            results[key[: -len(uuid_suffix)]] = orm.load_node(uuid=value)
        else:
            results[key] = value

    return results


class ProcessSubmitModel(pdt.BaseModel):
    label: str = pdt.Field(
        '',
        description='The label of the process',
        examples=['My process', 'Test calculation'],
    )
    entry_point: str = pdt.Field(
        description='The entry point of the process',
        examples=['core.arithmetic.add'],
    )
    inputs: dict[str, t.Any] = pdt.Field(
        description='The inputs of the process',
        examples=[{'x': 1, 'y': 2}],
    )

    @pdt.field_validator('inputs')
    @classmethod
    def validate_inputs(cls, inputs: dict[str, t.Any]) -> dict[str, t.Any]:
        """Process the inputs dictionary.

        :param inputs: The inputs to validate.
        :type inputs: dict[str, t.Any]
        :returns: The validated inputs.
        :rtype: dict[str, t.Any]
        """
        return process_inputs(inputs)


@write_router.post(
    '',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    responses={
        404: {'model': errors.NonExistentError},
        422: {'model': t.Union[errors.InvalidInputError, errors.InvalidOperationError]},
    },
)
@with_dbenv()
async def submit_process(
    process: ProcessSubmitModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> dict[str, t.Any]:
    """Submit new AiiDA process."""
    try:
        entry_point_process = load_entry_point_from_string(process.entry_point)
    except Exception as exception:
        raise exceptions.EntryPointError(str(exception)) from exception
    try:
        process_node = engine.submit(entry_point_process, **process.inputs)
    except Exception as exception:
        raise exceptions.InputValidationError(str(exception)) from exception
    return process_node.serialize(minimal=True)
