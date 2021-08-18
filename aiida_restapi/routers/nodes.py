# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, File, HTTPException
from importlib_metadata import entry_points

from aiida_restapi import models

from .auth import get_current_active_user

router = APIRouter()

ENTRY_POINTS = entry_points()


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

    qbobj.append(orm.Node, filters={"id": nodes_id}, project=["**"], tag="node").limit(
        1
    )
    return qbobj.dict()[0]["node"]


@router.post("/nodes", response_model=models.Node)
@with_dbenv()
async def create_node(
    node: models.Node_Post,
    current_user: models.User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> models.Node:
    """Create new AiiDA node."""

    node_dict = node.dict(exclude_unset=True)
    node_type = node_dict.pop("node_type", None)

    try:
        (entry_point_node,) = ENTRY_POINTS.select(
            group="aiida.rest.post", name=node_type
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail="Entry point '{}' not recognized.".format(node_type)
        ) from exc

    try:
        orm_object = entry_point_node.load().create_new_node(node_type, node_dict)
    except (TypeError, ValueError, KeyError) as err:
        raise HTTPException(status_code=400, detail="Error: {0}".format(err)) from err

    return models.Node.from_orm(orm_object)


@router.post("/singlefiledata", response_model=models.Node)
@with_dbenv()
async def create_upload_file(
    upload_file: bytes = File(...),
    params: models.Node_Post = Depends(models.Node_Post.as_form),  # type: ignore # pylint: disable=maybe-no-member
    current_user: models.User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> models.Node:
    """Endpoint for uploading file data"""
    node_dict = params.dict(exclude_unset=True, exclude_none=True)
    node_type = node_dict.pop("node_type", None)

    try:
        (entry_point_node,) = entry_points(group="aiida.rest.post", name=node_type)
    except KeyError as exc:
        raise KeyError("Entry point '{}' not recognized.".format(node_type)) from exc

    orm_object = entry_point_node.load().create_new_node_with_file(
        node_type, node_dict, upload_file
    )

    return models.Node.from_orm(orm_object)
