"""Declaration of FastAPI application."""

from __future__ import annotations

import re
import warnings

from aiida import __version__ as aiida_version
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from aiida_restapi.config import API_CONFIG
from aiida_restapi.models.server import ServerEndpoint, ServerInfo

read_router = APIRouter(prefix='/server')


@read_router.get(
    '/info',
    response_model=ServerInfo,
)
async def get_server_info() -> dict[str, str]:
    """Get the API version information."""
    api_version = API_CONFIG['VERSION'].split('.')
    return {
        'api_major_version': api_version[0],
        'api_minor_version': api_version[1],
        'api_revision_version': api_version[2],
        'api_prefix': API_CONFIG['PREFIX'],
        'aiida_version': aiida_version,
    }


@read_router.get(
    '/endpoints',
    response_model=dict[str, list[ServerEndpoint]],
)
async def get_server_endpoints(request: Request) -> dict[str, list[dict]]:
    """Get a JSON-serializable dictionary of all registered API routes."""
    return {
        'endpoints': [
            {key: value for key, value in endpoint.items() if key != 'disable_hyperlink'}
            for endpoint in _get_endpoints(request)
        ]
    }


@read_router.get(
    '/endpoints/table',
    name='endpoints',
    response_class=HTMLResponse,
)
async def get_server_endpoints_table(request: Request) -> HTMLResponse:
    """Get an HTML table of all registered API routes."""
    rows = []
    for endpoint in _get_endpoints(request):
        path = endpoint['path']
        group = endpoint['group']
        methods = endpoint['methods']
        description = endpoint['description']
        disable_hyperlink = endpoint['disable_hyperlink']

        path_row = path if disable_hyperlink else f'<a href="{path}">{path}</a>'

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


def _get_endpoints(request: Request) -> list[dict]:
    """Build the endpoint list from FastAPI's public OpenAPI representation.

    For all endpoints, allow hyperlinks only for non-parameterized GET endpoints, for example
    >>> GET /docs  # allowed
    >>> GET /openapi.json  # allowed
    >>> GET /users/{user_id}  # not allowed
    >>> POST /users  # not allowed
    """
    root_path = request.scope['root_path']
    endpoints: list[dict] = []

    # TODO remove once the issue is fixed in FastAPI
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore',
            message=r"The 'alias' attribute .* was provided to the `Field\(\)` function",
            category=Warning,
            module=r'pydantic\._internal\._generate_schema',
        )
        documented_paths = request.app.openapi()['paths']

    # Include built-in routes (excluding authentication routes)
    for route in request.app.routes:
        path = getattr(route, 'path', None)
        if path is None or path == '/' or path in documented_paths or 'auth' in path:
            continue

        methods = getattr(route, 'methods', None) or set()
        if not methods:
            continue

        endpoint_route = getattr(route, 'endpoint', None)
        route_docs = getattr(endpoint_route, '__doc__', None) or ''
        description = route_docs.split('\n')[0].strip()

        endpoints.append(
            {
                'path': root_path + path,
                'group': _get_route_group(path),
                'methods': methods,
                'description': description,
                'disable_hyperlink': bool(methods & {'POST'}) or '{' in path,
            }
        )

    # Include documented OpenAPI paths
    for path, path_item in documented_paths.items():
        for method, operation in path_item.items():
            parameters = operation.get('parameters', [])
            request_body = operation.get('requestBody', {})
            required_input = any(parameter.get('required', False) for parameter in parameters) or request_body.get(
                'required', False
            )
            description = (operation.get('description') or operation.get('summary') or '').split('\n')[0].strip()
            endpoints.append(
                {
                    'path': root_path + path,
                    'group': _get_route_group(path),
                    'methods': {method.upper()},
                    'description': description,
                    'disable_hyperlink': required_input or method == 'post' or '{' in path,
                }
            )

    graphql_path = f'{API_CONFIG["PREFIX"]}/graphql'
    if graphql_path not in documented_paths:
        endpoints.append(
            {
                'path': root_path + graphql_path,
                'group': 'graphql',
                'methods': {'POST'},
                'description': 'GraphQL endpoint.',
                'disable_hyperlink': True,
            }
        )

    return endpoints


def _get_route_group(path: str) -> str | None:
    """Return the group of an endpoint path."""
    prefix = re.escape(API_CONFIG['PREFIX'])
    match = re.match(rf'^{prefix}/([^/]+)/?.*', path)
    return match.group(1) if match else None
