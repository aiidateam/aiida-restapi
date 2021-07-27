# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""


from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, File
from importlib_metadata import entry_points

from aiida_restapi import models

from .auth import get_current_active_user

router = APIRouter()


@router.post("/nodes", response_model=models.Node)
@with_dbenv()
async def create_node(
    node: models.Node,
    current_user: models.User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> models.Node:
    """Create new AiiDA node."""

    node_dict = node.dict(exclude_unset=True)
    node_type = node_dict.pop("node_type", None)
    attributes = node_dict.pop("attributes", None)

    try:
        (entry_point_node,) = entry_points().select(
            group="aiida.rest.post", name=node_type
        )
    except KeyError as exc:
        raise KeyError("Entry point '{}' not recognized.".format(node_type)) from exc

    orm_object = entry_point_node.load().create_new_node(
        node_type, attributes, node_dict
    )

    return models.Node.from_orm(orm_object)


@router.post("/singlefiledata")
@with_dbenv()
async def create_upload_file(
    upload_file: bytes = File(...),
    params: models.Node = Depends(models.Node.as_form),  # type: ignore # pylint: disable=maybe-no-member
    current_user: models.User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> models.Node:
    """Test function for upload file will be merged with create_node later."""
    node_dict = params.dict(exclude_unset=True, exclude_none=True)
    node_type = node_dict.pop("node_type", None)
    attributes = node_dict.pop("attributes", {})

    try:
        (entry_point_node,) = entry_points(group="aiida.rest.post", name=node_type)
    except KeyError as exc:
        raise KeyError("Entry point '{}' not recognized.".format(node_type)) from exc

    orm_object = entry_point_node.load().create_new_node_with_file(
        node_type, attributes, node_dict, upload_file
    )

    return models.Node.from_orm(orm_object)
