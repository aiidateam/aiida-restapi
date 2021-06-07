# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.models import Group, User

from .auth import get_current_active_user

router = APIRouter()


@router.get("/groups", response_model=List[Group])
@with_dbenv()
async def read_groups() -> List[Group]:
    """Get list of all groups"""
    qbobj = orm.QueryBuilder().append(orm.Group, project=["**"])

    return [group["core_1"] for group in qbobj.dict()]


@router.get("/groups/{group_id}", response_model=Group)
@with_dbenv()
async def read_group(group_id: int) -> Optional[Group]:
    """Get group by id."""
    qbobj = orm.QueryBuilder()

    qbobj.append(orm.Group, filters={"id": group_id}, project=["**"]).limit(1)
    return qbobj.dict()[0]["core_1"]


@router.post("/groups", response_model=Group)
async def create_user(
    group: Group,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> Group:
    """Create new AiiDA group."""
    orm_group = orm.Group(**group.dict(exclude_unset=True)).store()
    return Group.from_orm(orm_group)
