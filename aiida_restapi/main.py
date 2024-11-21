"""Declaration of FastAPI application."""

from typing import Any

from fastapi import FastAPI

from aiida_restapi.config import API_CONFIG
from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, process, server, users

app = FastAPI()
app.include_router(auth.router)
app.include_router(computers.router)
app.include_router(daemon.router)
app.include_router(nodes.router)
app.include_router(groups.router)
app.include_router(users.router)
app.include_router(process.router)
app.add_route('/graphql', main.app, name='graphql')


# We need to create this endpoint here instead of in the server to avoid circular imports, since it is dependent on the
# app
@server.router.get('/server/endpoints', response_model=dict[str, Any])
async def get_server_endpoints() -> dict[str, Any]:
    """List available routes"""
    import re

    from fastapi.routing import APIRoute

    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            full_path = API_CONFIG['PREFIX'] + route.path
            match = re.search(r'^\/([^\/]+)', route.path)
            endpoint_group = None if match is None else match.group(1)
            routes.append(
                {
                    'path': full_path,
                    'group': endpoint_group,
                    'methods': route.methods,
                }
            )
    return {'endpoints': routes}


app.include_router(server.router)
