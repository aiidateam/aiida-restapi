"""Declaration of FastAPI application."""

import os
from json import JSONDecodeError

import pydantic as pdt
from aiida.common import exceptions as aiida_exceptions
from aiida.engine.daemon.client import DaemonException
from fastapi import APIRouter, FastAPI, Request
from fastapi import exceptions as fastapi_exceptions
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from aiida_restapi.common import exceptions as restapi_exceptions
from aiida_restapi.common.responses import JsonApiResponse
from aiida_restapi.common.types import RequestValidationErrorHandler
from aiida_restapi.config import API_CONFIG, load_config
from aiida_restapi.graphql import main
from aiida_restapi.jsonapi.errors import jsonapi_error
from aiida_restapi.routers import computers, daemon, groups, nodes, querybuilder, server, submit, tests, users


def create_app() -> FastAPI:
    """Create the FastAPI application and include the routers.

    :return: The FastAPI application.
    :rtype: FastAPI
    """

    root_path = os.getenv('AIIDA_RESTAPI_ROOT_PATH', '')
    read_only = os.getenv('AIIDA_RESTAPI_READ_ONLY') == '1'
    config = load_config()

    app = FastAPI()
    app.state.api_path = f'{root_path}{API_CONFIG["PREFIX"]}'

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=config.cors.allow_origin_regex,
        allow_origins=config.cors.allow_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    api_router = APIRouter(prefix=API_CONFIG['PREFIX'])

    api_router.add_route(
        '/',
        lambda _: RedirectResponse(url=api_router.url_path_for('endpoints')),
    )

    api_router.add_route(
        API_CONFIG['PREFIX'],
        lambda _: RedirectResponse(url=api_router.url_path_for('endpoints')),
    )

    request_validation_error_handlers: list[RequestValidationErrorHandler] = []
    for module in (server, users, computers, groups, nodes, querybuilder, submit, daemon, tests):
        if hasattr(module, 'handle_request_validation_errors'):
            request_validation_error_handlers.append(module.handle_request_validation_errors)
        if read_router := getattr(module, 'read_router', None):
            api_router.include_router(read_router)
        if not read_only and (write_router := getattr(module, 'write_router', None)):
            api_router.include_router(write_router)

    api_router.add_route(
        f'{API_CONFIG["PREFIX"]}/graphql',
        main.app,
        methods=['POST'],
    )

    app.include_router(api_router)

    app.exception_handlers |= {
        error_class: lambda req, exc, sc=status_code: jsonapi_error(req, exc, sc)
        for error_class, status_code in {
            JSONDecodeError: 400,
            aiida_exceptions.StoringNotAllowed: 403,
            aiida_exceptions.NotExistent: 404,
            FileNotFoundError: 404,
            aiida_exceptions.MultipleObjectsError: 409,
            aiida_exceptions.ValidationError: 422,
            pdt.ValidationError: 422,
            fastapi_exceptions.ValidationException: 422,
            restapi_exceptions.InvalidRequestError: 422,
            aiida_exceptions.InvalidOperation: 422,
            aiida_exceptions.EntryPointError: 422,
            aiida_exceptions.MissingEntryPointError: 422,
            aiida_exceptions.DbContentError: 422,
            aiida_exceptions.InputValidationError: 422,
            aiida_exceptions.ContentNotExistent: 422,
            restapi_exceptions.SchemaNotSupported: 422,
            aiida_exceptions.UnsupportedSchemaError: 422,
            restapi_exceptions.QueryBuilderException: 422,
            aiida_exceptions.LicensingException: 451,
            restapi_exceptions.JsonApiException: 500,
            DaemonException: 500,
            Exception: 500,
        }.items()
    }

    async def handle_request_validation_error(
        request: Request,
        exception: fastapi_exceptions.RequestValidationError,
    ) -> JsonApiResponse:
        """Handle request validation errors.

        :param request: The request that caused the validation error.
        :type request: Request
        :param exception: The validation error exception.
        :type exception: fastapi_exceptions.RequestValidationError
        :return: A JSON response containing the error in JSON:API format.
        :rtype: JsonApiResponse
        """
        for handler in request_validation_error_handlers:
            response = handler(request, exception)
            if response is not None:
                return response
        return jsonapi_error(request, exception, 422)

    app.exception_handlers[fastapi_exceptions.RequestValidationError] = handle_request_validation_error

    return app
