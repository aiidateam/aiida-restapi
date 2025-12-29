"""Declaration of FastAPI application."""

import os
from json import JSONDecodeError

import pydantic as pdt
from aiida.common import exceptions as aiida_exceptions
from aiida.engine.daemon.client import DaemonException
from fastapi import APIRouter, FastAPI
from fastapi import exceptions as fastapi_exceptions
from fastapi.responses import JSONResponse, RedirectResponse

from aiida_restapi.common import exceptions as restapi_exceptions
from aiida_restapi.config import API_CONFIG
from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, querybuilder, server, submit, users


def create_app() -> FastAPI:
    """Create the FastAPI application and include the routers.

    :return: The FastAPI application.
    :rtype: FastAPI
    """

    read_only = os.getenv('AIIDA_RESTAPI_READ_ONLY') == '1'

    app = FastAPI()

    api_router = APIRouter(prefix=API_CONFIG['PREFIX'])

    api_router.add_route(
        '/',
        lambda _: RedirectResponse(url=api_router.url_path_for('endpoints')),
    )

    for module in (auth, server, users, computers, groups, nodes, querybuilder, submit, daemon):
        if read_router := getattr(module, 'read_router', None):
            api_router.include_router(read_router)
        if not read_only and (write_router := getattr(module, 'write_router', None)):
            api_router.include_router(write_router)

    api_router.add_route(
        '/graphql',
        main.app,
        methods=['POST'],
    )

    app.include_router(api_router)

    app.exception_handlers |= {
        error_class: lambda _, exception, sc=status_code: JSONResponse(
            status_code=sc,
            content={'detail': str(exception)},
        )
        for error_class, status_code in {
            JSONDecodeError: 400,
            aiida_exceptions.StoringNotAllowed: 403,
            aiida_exceptions.NotExistent: 404,
            FileNotFoundError: 404,
            aiida_exceptions.MultipleObjectsError: 409,
            aiida_exceptions.ValidationError: 422,
            pdt.ValidationError: 422,
            fastapi_exceptions.ValidationException: 422,
            aiida_exceptions.InvalidOperation: 422,
            aiida_exceptions.EntryPointError: 422,
            aiida_exceptions.MissingEntryPointError: 422,
            aiida_exceptions.DbContentError: 422,
            aiida_exceptions.InputValidationError: 422,
            aiida_exceptions.ContentNotExistent: 422,
            restapi_exceptions.QueryBuilderException: 422,
            aiida_exceptions.LicensingException: 451,
            DaemonException: 500,
        }.items()
    }

    return app
