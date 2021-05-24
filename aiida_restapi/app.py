# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List
from fastapi import FastAPI
from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida_restapi.models import User

app = FastAPI()


@app.get('/users', response_model=List[User])
@with_dbenv()
async def read_users():
    """Get list of all users"""
    return [User.from_orm(u) for u in orm.User.objects.find()]


@app.get('/users/{user_id}', response_model=User)
@with_dbenv()
async def read_user(user_id: int):
    """Get user by id."""
    orm_user = orm.User.objects.get(id=user_id)

    if orm_user:
        return User.from_orm(orm_user)

    return None


@app.post('/users', response_model=User)
async def create_user(user: User):
    """Create new AiiDA user."""
    orm_user = orm.User(**user.dict(exclude_unset=True)).store()
    return User.from_orm(orm_user)
