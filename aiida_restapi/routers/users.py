# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.models import User

from .auth import get_current_active_user

router = APIRouter()


@router.get("/users", response_model=List[User])
@with_dbenv()
async def read_users() -> List[User]:
    """Get list of all users"""
    return [User.from_orm(u) for u in orm.User.objects.find()]


@router.get("/users/{user_id}", response_model=User)
@with_dbenv()
async def read_user(user_id: int) -> Optional[User]:
    """Get user by id."""
    orm_user = orm.User.objects.get(id=user_id)

    if orm_user:
        return User.from_orm(orm_user)

    return None


@router.post("/users", response_model=User)
async def create_user(
    user: User,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> User:
    """Create new AiiDA user."""
    orm_user = orm.User(**user.dict(exclude_unset=True)).store()
    return User.from_orm(orm_user)
