"""Declaration of FastAPI application."""

from fastapi import FastAPI

from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, process, users

from .middleware import protected_methods_middleware

app = FastAPI()

app.middleware('http')(protected_methods_middleware)

app.include_router(auth.router)
app.include_router(computers.router)
app.include_router(daemon.router)
app.include_router(nodes.router)
app.include_router(groups.router)
app.include_router(users.router)
app.include_router(process.router)
app.add_route('/graphql', main.app, name='graphql')
