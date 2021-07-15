# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""

try:
    from importlib import metadata
except ImportError:  # for Python<3.8
    import importlib_metadata as metadata  # type: ignore[no-redef]

from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, File

from aiida_restapi.models import Node, User

from .auth import get_current_active_user

router = APIRouter()


@router.post("/nodes", response_model=Node)
@with_dbenv()
async def create_node(
    node: Node,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> Node:
    """Create new AiiDA node."""

    node_dict = node.dict(exclude_unset=True)
    node_type = node_dict.pop("node_type", None)
    attributes = node_dict.pop("attributes", None)

    entry_point_nodes = metadata.entry_points()["aiida.rest.post"]

    for ep_node in entry_point_nodes:
        if ep_node.name == node_type:
            orm_object = ep_node.load().create_new_node(
                node_type, attributes, node_dict
            )

    return Node.from_orm(orm_object)


@router.post("/singlefiledata")
@with_dbenv()
async def create_upload_file(
    upload_file: bytes = File(...),
    params: Node = Depends(Node.as_form),  # type: ignore # pylint: disable=maybe-no-member
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> Node:
    """Test function for upload file will be merged with create_node later."""
    node_dict = params.dict(exclude_unset=True, exclude_none=True)
    node_type = node_dict.pop("node_type", None)
    attributes = node_dict.pop("attributes", {})

    entry_point_nodes = metadata.entry_points()["aiida.rest.post"]

    for ep_node in entry_point_nodes:
        if ep_node.name == node_type:
            orm_object = ep_node.load().create_new_node_with_file(
                node_type, attributes, node_dict, upload_file
            )

    return Node.from_orm(orm_object)
