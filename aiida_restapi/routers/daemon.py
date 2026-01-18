"""Declaration of FastAPI router for daemon endpoints."""

from __future__ import annotations

import typing as t

from aiida.cmdline.utils.decorators import with_dbenv
from aiida.engine.daemon.client import DaemonException, get_daemon_client
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from aiida_restapi.jsonapi.models import errors

from .auth import UserInDB, get_current_active_user

read_router = APIRouter(prefix='/daemon')
write_router = APIRouter(prefix='/daemon')


class DaemonStatusModel(BaseModel):
    """Response model for daemon status."""

    running: bool = Field(description='Whether the daemon is running or not.')
    num_workers: t.Optional[int] = Field(description='The number of workers if the daemon is running.')


@read_router.get(
    '/status',
    response_model=DaemonStatusModel,
    responses={
        500: {'model': errors.DaemonError},
    },
)
@with_dbenv()
async def get_daemon_status() -> DaemonStatusModel:
    """Return the daemon status."""
    client = get_daemon_client()

    if not client.is_daemon_running:
        return DaemonStatusModel(running=False, num_workers=None)

    response = client.get_numprocesses()

    return DaemonStatusModel(running=True, num_workers=response['numprocesses'])


@write_router.post(
    '/start',
    response_model=DaemonStatusModel,
    responses={
        500: {'model': errors.DaemonError},
    },
)
@with_dbenv()
async def get_daemon_start(
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> DaemonStatusModel:
    """Start the daemon."""
    client = get_daemon_client()

    if client.is_daemon_running:
        raise DaemonException('The daemon is already running.')

    client.start_daemon()
    response = client.get_numprocesses()

    return DaemonStatusModel(running=True, num_workers=response['numprocesses'])


@write_router.post(
    '/stop',
    response_model=DaemonStatusModel,
    responses={
        500: {'model': errors.DaemonError},
    },
)
@with_dbenv()
async def get_daemon_stop(
    current_user: t.Annotated[UserInDB, Depends(get_current_active_user)],
) -> DaemonStatusModel:
    """Stop the daemon."""
    client = get_daemon_client()

    if not client.is_daemon_running:
        raise DaemonException('The daemon is not running.')

    client.stop_daemon()

    return DaemonStatusModel(running=False, num_workers=None)
