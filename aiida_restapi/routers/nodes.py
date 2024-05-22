# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import EntryPointError
from aiida.plugins.entry_point import load_entry_point
from fastapi import APIRouter, Depends, File, HTTPException

from aiida_restapi import models

from .auth import get_current_active_user

router = APIRouter()


@router.get("/nodes", response_model=List[models.Node])
@with_dbenv()
async def read_nodes() -> List[models.Node]:
    """Get list of all nodes"""
    return models.Node.get_entities()


@router.get("/nodes/projectable_properties", response_model=List[str])
async def get_nodes_projectable_properties() -> List[str]:
    """Get projectable properties for nodes endpoint"""

    return models.Node.get_projectable_properties()


@router.get("/nodes/{nodes_id}", response_model=models.Node)
@with_dbenv()
async def read_node(nodes_id: int) -> Optional[models.Node]:
    """Get nodes by id."""
    qbobj = orm.QueryBuilder()
    qbobj.append(orm.Node, filters={"id": nodes_id}, project="**", tag="node").limit(1)
    return qbobj.dict()[0]["node"]


@router.post("/nodes", response_model=models.Node)
@with_dbenv()
async def create_node(
    node: models.Node_Post,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Node:
    """Create new AiiDA node."""
    node_dict = node.dict(exclude_unset=True)
    entry_point = node_dict.pop("entry_point", None)

    try:
        cls = load_entry_point(group="aiida.data", name=entry_point)
    except EntryPointError as exception:
        raise HTTPException(status_code=404, detail=str(exception)) from exception

    try:
        orm_object = models.Node_Post.create_new_node(cls, node_dict)
    except (TypeError, ValueError, KeyError) as exception:
        raise HTTPException(status_code=400, detail=str(exception)) from exception

    return models.Node.from_orm(orm_object)


@router.post("/nodes/singlefile", response_model=models.Node)
@with_dbenv()
async def create_upload_file(
    upload_file: bytes = File(...),
    params: models.Node_Post = Depends(models.Node_Post.as_form),  # type: ignore # pylint: disable=maybe-no-member
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Node:
    """Endpoint for uploading file data"""
    node_dict = params.dict(exclude_unset=True, exclude_none=True)
    entry_point = node_dict.pop("entry_point", None)

    try:
        cls = load_entry_point(group="aiida.data", name=entry_point)
    except EntryPointError as exception:
        raise HTTPException(
            status_code=404,
            detail=f"Could not load entry point: {exception}",
        ) from exception

    orm_object = models.Node_Post.create_new_node_with_file(cls, node_dict, upload_file)

    return models.Node.from_orm(orm_object)
