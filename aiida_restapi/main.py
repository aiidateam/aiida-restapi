"""Declaration of FastAPI application."""

import os

from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse

from aiida_restapi.config import API_CONFIG
from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, server, submit, users


def create_app() -> FastAPI:
    """Create the FastAPI application and include the routers."""

    read_only = os.getenv('AIIDA_RESTAPI_READ_ONLY') == '1'

    app = FastAPI()

    api_router = APIRouter(prefix=API_CONFIG['PREFIX'])

    for module in (auth, computers, daemon, groups, nodes, server, submit, users):
        if read_router := getattr(module, 'read_router', None):
            api_router.include_router(read_router)
        if not read_only and (write_router := getattr(module, 'write_router', None)):
            api_router.include_router(write_router)

    api_router.add_route(
        '/graphql',
        main.app,
        methods=['POST'],
    )

    api_router.add_route(
        '/',
        lambda _: RedirectResponse(url=api_router.url_path_for('endpoints')),
    )

    app.include_router(api_router)

    return app
