# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter, Depends

from aiida_restapi.models import User

from .auth import get_current_active_user

router = APIRouter()


@router.get("/users", response_model=List[User])
@with_dbenv()
async def read_users() -> List[User]:
    """Get list of all users"""
    return User.get_entities()


@router.get("/users/projectable_properties", response_model=List[str])
async def get_users_projectable_properties() -> List[str]:
    """Get projectable properties for users endpoint"""

    return User.get_projectable_properties()


@router.get("/users/{user_id}", response_model=User)
@with_dbenv()
async def read_user(user_id: int) -> Optional[User]:
    """Get user by id."""
    qbobj = QueryBuilder()
    qbobj.append(orm.User, filters={"id": user_id}, project="**", tag="user").limit(1)

    return qbobj.dict()[0]["user"]


@router.post("/users", response_model=User)
@with_dbenv()
async def create_user(
    user: User,
    current_user: User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> User:
    """Create new AiiDA user."""
    orm_user = orm.User(**user.dict(exclude_unset=True)).store()
    return User.from_orm(orm_user)
