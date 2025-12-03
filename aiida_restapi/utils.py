"""General utility functions."""

import datetime

from dateutil.parser import parser as date_parser
from fastapi.routing import APIRoute
from starlette.routing import Route


def parse_date(string: str) -> datetime.datetime:
    """Parse any date/time stamp string."""
    return date_parser().parse(string)


def generate_endpoints_table(base_url: str, routes: list[Route]) -> str:
    """Return an HTML table string of all registered API routes.

    :param base_url: The base URL to prepend to each route path.
    :param routes: A list of FastAPI/Starlette Route objects.
    :return: An HTML string representing the table of endpoints.
    """
    rows = []

    for route in routes:
        if route.path == '/':
            continue

        path = f'{base_url}{route.path}'
        methods = ', '.join(sorted((route.methods - {'HEAD', 'OPTIONS'}) if route.methods else {}))
        summary = 'Post graphQL query' if 'graphql' in path else (route.endpoint.__doc__ or '').split('\n')[0].strip()

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
            <td>{methods}</td>
            <td>{summary or '-'}</td>
        </tr>
        """)

    return f"""
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
                    <tr>
                        <th>URL</th>
                        <th>Methods</th>
                        <th>Summary</th>
                    </tr>
                    {''.join(rows)}
                </table>
            </body>
        </html>
    """
