# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.models import Group, Group_Post, User

from .auth import get_current_active_user

router = APIRouter()


@router.get("/groups", response_model=List[Group])
@with_dbenv()
async def read_groups() -> List[Group]:
    """Get list of all groups"""

    return Group.get_entities()


@router.get("/groups/projectable_properties", response_model=List[str])
async def get_groups_projectable_properties() -> List[str]:
    """Get projectable properties for groups endpoint"""

    return Group.get_projectable_properties()


@router.get("/groups/{group_id}", response_model=Group)
@with_dbenv()
async def read_group(group_id: int) -> Optional[Group]:
    """Get group by id."""
    qbobj = orm.QueryBuilder()

    qbobj.append(orm.Group, filters={"id": group_id}, project="**", tag="group").limit(
        1
    )
    return qbobj.dict()[0]["group"]


@router.post("/groups", response_model=Group)
@with_dbenv()
async def create_group(
    group: Group_Post,
    current_user: User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> Group:
    """Create new AiiDA group."""
    orm_group = orm.Group(**group.dict(exclude_unset=True)).store()
    return Group.from_orm(orm_group)
