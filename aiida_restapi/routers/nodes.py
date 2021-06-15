# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""


from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends, HTTPException

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
    node_options = {
        "Int": orm.Int,
        "Float": orm.Float,
        "String": orm.Str,
        "Dict": orm.Dict,
        "List": orm.List,
        "Bool": orm.Bool,
        "StructureData": orm.StructureData,
    }

    if node_type not in node_options.keys():
        raise HTTPException(status_code=404, detail="Node type not found")

    orm_object = node_options[node_type](**node_dict)

    for key, value in attributes.items():
        orm_object.set_attribute(key, value)

    return Node.from_orm(orm_object)
