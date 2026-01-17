"""Declaration of FastAPI application."""

from __future__ import annotations

import re

import pydantic as pdt
from aiida import __version__ as aiida_version
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from starlette.routing import Route

from aiida_restapi.config import API_CONFIG

read_router = APIRouter(prefix='/server')


class ServerInfo(pdt.BaseModel):
    """API version information."""

    API_major_version: str = pdt.Field(
        description='Major version of the API',
        examples=['0'],
    )
    API_minor_version: str = pdt.Field(
        description='Minor version of the API',
        examples=['1'],
    )
    API_revision_version: str = pdt.Field(
        description='Revision version of the API',
        examples=['0a1'],
    )
    API_prefix: str = pdt.Field(
        description='Prefix for all API endpoints',
        examples=['/api/v0'],
    )
    AiiDA_version: str = pdt.Field(
        description='Version of the AiiDA installation',
        examples=['2.7.2.post0'],
    )


@read_router.get(
    '/info',
    response_model=ServerInfo,
)
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

    path: str = pdt.Field(
        description='Path of the endpoint',
        examples=['../server/endpoints'],
    )
    group: str | None = pdt.Field(
        description='Group of the endpoint',
        examples=['server'],
    )
    methods: set[str] = pdt.Field(
        description='HTTP methods supported by the endpoint',
        examples=['GET'],
    )
    description: str = pdt.Field(
        '-',
        description='Description of the endpoint',
        examples=['Get a JSON-serializable dictionary of all registered API routes.'],
    )


@read_router.get(
    '/endpoints',
    response_model=dict[str, list[ServerEndpoint]],
)
async def get_server_endpoints(request: Request) -> dict[str, list[ServerEndpoint]]:
    """Get a JSON-serializable dictionary of all registered API routes."""
    endpoints: list[ServerEndpoint] = []

    for route in request.app.routes:
        if route.path == '/':
            continue

        group, methods, description = _get_route_parts(route)
        base_url = str(request.base_url).rstrip('/')

        endpoint = {
            'path': base_url + route.path,
            'group': group,
            'methods': methods,
            'description': description,
        }

        endpoints.append(ServerEndpoint(**endpoint))

    return {'endpoints': endpoints}


@read_router.get(
    '/endpoints/table',
    name='endpoints',
    response_class=HTMLResponse,
)
async def get_server_endpoints_table(request: Request) -> HTMLResponse:
    """Get an HTML table of all registered API routes."""
    routes = request.app.routes
    base_url = str(request.base_url).rstrip('/')

    rows = []

    for route in routes:
        if route.path == '/':
            continue

        path = base_url + route.path
        group, methods, description = _get_route_parts(route)

        disable_url = (
            (
                isinstance(route, APIRoute)
                and any(
                    param
                    for param in route.dependant.path_params
                    + route.dependant.query_params
                    + route.dependant.body_params
                    if param.required
                )
            )
            or (route.methods and 'POST' in route.methods)
            or 'auth' in path
        )

        path_row = path if disable_url else f'<a href="{path}">{path}</a>'

        rows.append(f"""
        <tr>
            <td>{path_row}</td>
            <td>{group or '-'}</td>
            <td>{', '.join(methods)}</td>
            <td>{description or '-'}</td>
        </tr>
        """)

    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>AiiDA REST API Endpoints</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                        padding: 1em;
                        color: #222;
                    }}
                    h1 {{
                        margin-bottom: 0.5em;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 0.5em 0.75em;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f4f4f4;
                    }}
                    tr:nth-child(even) {{
                        background-color: #fafafa;
                    }}
                    tr:hover {{
                        background-color: #f1f1f1;
                    }}
                    a {{
                        text-decoration: none;
                        color: #0066cc;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <h1>AiiDA REST API Endpoints</h1>
                <table>
                    <thead>
                        <tr>
                            <th>URL</th>
                            <th>Group</th>
                            <th>Methods</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows)}
                    </tbody>
                </table>
            </body>
        </html>
    """
    )


def _get_route_parts(route: Route) -> tuple[str | None, set[str], str]:
    """Return the parts of a route: path, group, methods, description.

    :param route: A FastAPI/Starlette Route object.
    :return: A tuple containing the group, methods, and description of the route.
    """
    prefix = re.escape(API_CONFIG['PREFIX'])
    match = re.match(rf'^{prefix}/([^/]+)/?.*', route.path)
    group = match.group(1) if match else None
    methods = (route.methods or set()) - {'HEAD', 'OPTIONS'}
    description = (route.endpoint.__doc__ or '').split('\n')[0].strip()
    return group, methods, description
