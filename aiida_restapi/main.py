"""Declaration of FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from aiida_restapi.graphql import main
from aiida_restapi.routers import auth, computers, daemon, groups, nodes, submit, users
from aiida_restapi.utils import generate_endpoints_table

app = FastAPI()


@app.get('/', response_class=HTMLResponse)
def list_endpoints(request: Request) -> HTMLResponse:
    """Return an HTML table of all registered API routes."""
    return HTMLResponse(
        content=generate_endpoints_table(
            str(request.base_url).rstrip('/'),
            app.routes,
        ),
    )


app.include_router(auth.router)
app.include_router(computers.router)
app.include_router(daemon.router)
app.include_router(nodes.router)
app.include_router(groups.router)
app.include_router(users.router)
app.include_router(submit.router)

app.add_route('/graphql', main.app, name='graphql', methods=['POST'])
