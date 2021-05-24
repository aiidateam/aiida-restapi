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
async def users():
    """Get list of all users"""
    return [User.from_orm(u) for u in orm.User.objects.find()]


@app.get('/users/{user_id}')
@with_dbenv()
async def user(user_id: int):
    """Get user by id."""
    orm_user = orm.User.objects.get(id=user_id)

    if orm_user:
        return User.from_orm(orm_user)

    return None
