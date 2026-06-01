from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from aiida_restapi.config import API_CONFIG
from aiida_restapi.routers.nodes import model_registry

read_router = APIRouter(prefix='/tests')
write_router = APIRouter(prefix='/tests')

here = Path(__file__).parent
templates = Jinja2Templates(str(here / 'templates'))
css = here / 'styles.css'


@write_router.get('/nodes/post', response_class=HTMLResponse)
async def test_nodes_post(request: Request) -> HTMLResponse:
    """Serve page to test node POST requests."""
    node_types = '\n'.join(
        f'<option value="{model_cls}">{model_cls}</option>' for model_cls in sorted(model_registry.get_node_types())
    )
    return templates.TemplateResponse(
        'node_post.html',
        {
            'request': request,
            'css': css.read_text(),
            'api_prefix': API_CONFIG['PREFIX'],
            'options': node_types,
        },
    )


@read_router.get('/querybuilder', response_class=HTMLResponse)
async def test_querybuilder(request: Request) -> HTMLResponse:
    """Serve page to test query builder endpoint."""
    return templates.TemplateResponse(
        'querybuilder.html',
        {
            'request': request,
            'css': css.read_text(),
            'api_prefix': API_CONFIG['PREFIX'],
        },
    )
