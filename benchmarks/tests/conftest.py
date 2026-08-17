"""Benchmark-specific fixtures.

Overrides the default AiiDA profile and database-clearing fixtures so
benchmarks run against the pre-seeded ``benchmark-restapi`` profile
without wiping data between tests.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from aiida_restapi.config import API_CONFIG
from aiida_restapi.main import create_app

pytest_plugins = ['aiida.tools.pytest_fixtures']


# ---------------------------------------------------------------------------
# Middleware (mirrors tests/conftest.py)
# ---------------------------------------------------------------------------

class PrefixMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, prefix: str = ''):
        super().__init__(app)
        self.prefix = prefix or API_CONFIG['PREFIX']

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(self.prefix):
            request.scope['path'] = self.prefix + request.url.path
        return await call_next(request)


# ---------------------------------------------------------------------------
# AiiDA profile -- load the pre-seeded benchmark profile
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session', autouse=True)
def aiida_config():
    """No-op: use the real AiiDA config, not a temporary one."""


@pytest.fixture(scope='session', autouse=True)
def aiida_profile():
    """Load the pre-existing benchmark profile instead of creating a fresh one."""
    from aiida import load_profile

    profile = load_profile('benchmark-restapi')
    yield profile


@pytest.fixture(scope='function', autouse=True)
def clear_database_auto():
    """No-op: keep the seeded data intact across benchmarks."""


# ---------------------------------------------------------------------------
# FastAPI app & HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.add_middleware(PrefixMiddleware)
    yield app


@pytest.fixture(scope='function')
def client(app):
    return TestClient(app)
