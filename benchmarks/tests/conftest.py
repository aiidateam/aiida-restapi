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

pytest_plugins = ['aiida.tools.pytest_fixtures']

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
# Benchmark helper -- measures response size alongside latency
# ---------------------------------------------------------------------------

def _bench(benchmark, client, method, url, **kwargs):
    """Run *benchmark* while recording response size as extra_info.

    Usage::

        _bench(benchmark, client, 'get', '/nodes?page_size=50')
        _bench(benchmark, client, 'post', '/querybuilder', json={...})
    """
    fn = getattr(client, method)
    resp = fn(url, **kwargs)
    benchmark.extra_info['response_bytes'] = len(resp.content)
    benchmark.extra_info['status_code'] = resp.status_code
    benchmark(fn, url, **kwargs)


# ---------------------------------------------------------------------------
# Write structured report after all tests finish
# ---------------------------------------------------------------------------

def pytest_sessionfinish(session, exitstatus):
    """Write benchmark results and breakdown data to ``breakdown_report.json``."""
    benchmark_session = session.config._benchmarksession
    if not benchmark_session:
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
            entry['response_bytes'] = bench.extra_info.get('response_bytes')
            entry['status_code'] = bench.extra_info.get('status_code')
        report['benchmarks'].append(entry)

    # Attach breakdown data collected by test_bench_breakdown
    breakdowns = []
    if _BREAKDOWN_PATH.exists():
        with open(_BREAKDOWN_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    breakdowns.append(json.loads(line))
    report['breakdowns'] = breakdowns

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f'\nBenchmark report written to {REPORT_PATH}')

    # Clean up temp breakdown data
    if _BREAKDOWN_PATH.exists():
        _BREAKDOWN_PATH.unlink()
