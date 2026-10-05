"""Benchmark-specific fixtures.

Overrides the default AiiDA profile and database-clearing fixtures so
benchmarks run against the pre-seeded ``benchmark-restapi`` profile
without wiping data between tests.
"""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from aiida_restapi.config import API_CONFIG
from aiida_restapi.main import create_app

# NOTE: `pytest_plugins = ['aiida.tools.pytest_fixtures']` lives in the
# root-level conftest.py (defining it here breaks bare `pytest` runs).

REPORT_PATH = Path(__file__).resolve().parent.parent / 'breakdown_report.json'
_BREAKDOWN_PATH = Path(__file__).resolve().parent.parent / '_breakdown_data.jsonl'


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
    # Clear stale breakdown data from previous runs
    if _BREAKDOWN_PATH.exists():
        _BREAKDOWN_PATH.unlink()


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


# ---------------------------------------------------------------------------
# Write structured report after all tests finish
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session, exitstatus):
    """Write benchmark results and breakdown data to ``breakdown_report.json``."""
    benchmark_session = getattr(session.config, '_benchmarksession', None)
    if not benchmark_session or not getattr(benchmark_session, 'benchmarks', None):
        return

    report = {
        'benchmarks': [],
        'breakdowns': [],
    }

    for bench in benchmark_session.benchmarks:
        entry = {
            'name': bench.name,
            'fullname': bench.fullname,
            'mean_ms': round(bench.stats.mean * 1000, 3),
            'min_ms': round(bench.stats.min * 1000, 3),
            'max_ms': round(bench.stats.max * 1000, 3),
            'stddev_ms': round(bench.stats.stddev * 1000, 3),
            'rounds': bench.stats.rounds,
            'ops_per_sec': round(1 / bench.stats.mean, 2) if bench.stats.mean > 0 else 0,
        }
        if hasattr(bench, 'extra_info'):
            extra = bench.extra_info or {}
            entry['response_bytes'] = extra.get('response_bytes')
            entry['status_code'] = extra.get('status_code')
        else:
            entry['response_bytes'] = None
            entry['status_code'] = None
        report['benchmarks'].append(entry)

    # Attach breakdown data collected by test_bench_breakdown
    breakdowns = []
    if _BREAKDOWN_PATH.exists():
        with open(_BREAKDOWN_PATH) as f:
            for raw_line in f:
                stripped = raw_line.strip()
                if stripped:
                    breakdowns.append(json.loads(stripped))
    report['breakdowns'] = breakdowns

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f'\nBenchmark report written to {REPORT_PATH}')

    # Clean up temp breakdown data
    if _BREAKDOWN_PATH.exists():
        _BREAKDOWN_PATH.unlink()
