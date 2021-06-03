# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.common.exceptions import NotExistent
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from aiida_restapi.models import EntityResponse, User

from .auth import get_current_active_user

__all__ = ("router",)

router = APIRouter()

SingleUserResponse = EntityResponse(User)
ManyUserResponse = EntityResponse(User, use_list=True)


@router.get("/users", response_model=ManyUserResponse)
@with_dbenv()
async def read_users() -> ManyUserResponse:
    """Get list of all users"""
    return ManyUserResponse(data=User.get_entities())


@router.get("/users/{user_id}", response_model=SingleUserResponse)
@with_dbenv()
async def read_user(user_id: int) -> SingleUserResponse:
    """Get user by id."""
    try:
        orm_user = orm.User.objects.get(id=user_id)
    except NotExistent as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc

    return SingleUserResponse(user=User.from_orm(orm_user))


@router.post("/users", response_model=SingleUserResponse)
@with_dbenv()
async def create_user(
    user: User,
    current_user: User = Depends(
        get_current_active_user
    ),  # pylint: disable=unused-argument
) -> SingleUserResponse:
    """Create new AiiDA user."""
    orm_user = orm.User(**user.dict(exclude_unset=True)).store()
    return SingleUserResponse(data=User.from_orm(orm_user))
