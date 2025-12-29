"""Declaration of FastAPI router for submission."""

from __future__ import annotations

import typing as t

import pydantic as pdt
from aiida import engine, orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from aiida.plugins.entry_point import load_entry_point_from_string
from fastapi import APIRouter, Depends, HTTPException

from .auth import UserInDB, get_current_active_user

write_router = APIRouter(prefix='/submit')


def process_inputs(inputs: dict[str, t.Any]) -> dict[str, t.Any]:
    """Process the inputs dictionary converting each node UUID into the corresponding node by loading it.

    A node UUID is indicated by the key ending with the suffix ``.uuid``.

    :param inputs: The inputs dictionary.
    :returns: The deserialized inputs dictionary.
    :raises HTTPException: 404 if the inputs contain a UUID that does not correspond to an existing node.
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
                raise HTTPException(status_code=404, detail=f'Node with UUID `{value}` does not exist.') from exc
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
        :returns: The validated inputs.
        """
        return process_inputs(inputs)


@write_router.post(
    '',
    response_model=orm.Node.Model,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
@with_dbenv()
async def submit_process(
    process: ProcessSubmitModel,
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> orm.Node.Model:
    """Submit new AiiDA process."""
    try:
        entry_point_process = load_entry_point_from_string(process.entry_point)
        process_node = engine.submit(entry_point_process, **process.inputs)
        return t.cast(orm.Node.Model, process_node.to_model())
    except ValueError as err:
        raise HTTPException(status_code=404, detail=f"Entry point '{process.entry_point}' not recognized.") from err
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err)) from err
