"""Declaration of FastAPI application."""

from __future__ import annotations

import re

import pydantic as pdt
from aiida import __version__ as aiida_version
from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

from aiida_restapi.config import API_CONFIG

router = APIRouter()


class ServerInfo(pdt.BaseModel):
    """API version information."""

    API_major_version: str = pdt.Field(description='Major version of the API')
    API_minor_version: str = pdt.Field(description='Minor version of the API')
    API_revision_version: str = pdt.Field(description='Revision version of the API')
    API_prefix: str = pdt.Field(description='Prefix for all API endpoints')
    AiiDA_version: str = pdt.Field(description='Version of the AiiDA installation')


@router.get('/server/info', response_model=ServerInfo)
async def get_server_info() -> ServerInfo:
    """Get the API version information."""
    api_version = API_CONFIG['VERSION'].split('.')
    return ServerInfo(
        API_major_version=api_version[0],
        API_minor_version=api_version[1],
        API_revision_version=api_version[2],
        API_prefix=API_CONFIG['PREFIX'],
        AiiDA_version=aiida_version,
    )


class ServerEndpoint(pdt.BaseModel):
    """API endpoint."""

    path: str = pdt.Field(description='Path of the endpoint')
    group: str | None = pdt.Field(description='Group of the endpoint')
    methods: set[str] = pdt.Field(description='HTTP methods supported by the endpoint')


@router.get('/server/endpoints', response_model=dict[str, list[ServerEndpoint]])
async def get_server_endpoints(request: Request) -> dict[str, list[ServerEndpoint]]:
    """List available routes."""

    routes: list[ServerEndpoint] = []
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            full_path = API_CONFIG['PREFIX'] + route.path
            match = re.search(r'^\/([^\/]+)', route.path)
            endpoint_group = None if match is None else match.group(1)
            endpoint = ServerEndpoint(
                path=full_path,
                group=endpoint_group,
                methods=route.methods,
            )
            routes.append(endpoint)

    return {'endpoints': routes}
