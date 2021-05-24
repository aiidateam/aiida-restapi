# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from fastapi import FastAPI
from aiida_restapi.routers import users, auth

app = FastAPI()
app.include_router(auth.router)
app.include_router(users.router)
