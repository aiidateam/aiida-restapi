# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from fastapi import APIRouter, Depends

from aiida_restapi.models import Response, User

from .auth import get_current_active_user

router = APIRouter()

UserResponse = Response(User)
UsersResponse = Response(User, use_list=True)
UsersResponse.update_forward_refs()

@router.get('/users', response_model=UsersResponse)
@with_dbenv()
async def read_users() -> UsersResponse:
    """Get list of all users"""
    #print(User.get_entities())
    #print(UserResponse({'data':User.get_entities()}))
    print(User.get_entities())
    return {'data' : User.get_entities() }
    #return UsersResponse(data=User.get_entities())


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
