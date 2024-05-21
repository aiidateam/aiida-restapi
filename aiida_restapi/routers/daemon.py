# -*- coding: utf-8 -*-
"""Declaration of FastAPI router for daemon endpoints."""
from __future__ import annotations

import typing as t

from aiida.cmdline.utils.decorators import with_dbenv
from aiida.engine.daemon.client import DaemonException, get_daemon_client
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..models import User
from .auth import get_current_active_user

router = APIRouter()


class DaemonStatusModel(BaseModel):
    """Response model for daemon status."""

    running: bool = Field(description="Whether the daemon is running or not.")
    num_workers: t.Optional[int] = Field(
        description="The number of workers if the daemon is running."
    )


@router.get("/daemon/status", response_model=DaemonStatusModel)
@with_dbenv()
async def get_daemon_status() -> DaemonStatusModel:
    """Return the daemon status."""
    client = get_daemon_client()

    if not client.is_daemon_running:
        return DaemonStatusModel(running=False, num_workers=None)

    response = client.get_numprocesses()

    return DaemonStatusModel(running=True, num_workers=response["numprocesses"])


@router.post("/daemon/start", response_model=DaemonStatusModel)
@with_dbenv()
async def get_daemon_start(
    current_user: User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> DaemonStatusModel:
    """Start the daemon."""
    client = get_daemon_client()

    if client.is_daemon_running:
        raise HTTPException(status_code=400, detail="The daemon is already running.")

    try:
        client.start_daemon()
    except DaemonException as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception

    response = client.get_numprocesses()

    return DaemonStatusModel(running=True, num_workers=response["numprocesses"])


@router.post("/daemon/stop", response_model=DaemonStatusModel)
@with_dbenv()
async def get_daemon_stop(
    current_user: User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> DaemonStatusModel:
    """Stop the daemon."""
    client = get_daemon_client()

    if not client.is_daemon_running:
        raise HTTPException(status_code=400, detail="The daemon is not running.")

    try:
        client.stop_daemon()
    except DaemonException as exception:
        raise HTTPException(status_code=500, detail=str(exception)) from exception

    return DaemonStatusModel(running=False, num_workers=None)
