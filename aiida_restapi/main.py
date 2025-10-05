"""Declaration of FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, submit, users
from aiida_restapi.utils import generate_endpoints_table


def generate_endpoints_table_endpoint(app: FastAPI):
    """Generate an endpoint that lists all registered API routes."""

    def list_endpoints(request: Request) -> HTMLResponse:
        """Return an HTML table of all registered API routes."""
        return HTMLResponse(
            content=generate_endpoints_table(
                str(request.base_url).rstrip('/'),
                app.routes,
            ),
        )

    return list_endpoints


def create_app(read_only: bool = False) -> FastAPI:
    """Create the FastAPI application and include the routers."""
    app = FastAPI()
    app.include_router(auth.router)

    for module in (computers, daemon, groups, nodes, submit, users):
        if read_router := getattr(module, 'read_router', None):
            app.include_router(read_router)
        if not read_only and (write_router := getattr(module, 'write_router', None)):
            app.include_router(write_router)

    app.add_route('/graphql', main.app)
    app.add_route('/', lambda request: generate_endpoints_table_endpoint(app)(request))

    return app
