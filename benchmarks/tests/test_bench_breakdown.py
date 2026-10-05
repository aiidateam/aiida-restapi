"""Benchmark breakdown: measures where time is spent per request.

Instead of only measuring total request latency, this test instruments
the internal layers (DB query, JSON:API serialization) so you can see
the percentage split.

Run with:
    pytest benchmarks/tests/test_bench_breakdown.py -v -s
"""

import functools
import json
from pathlib import Path

import pytest

from benchmarks.helpers import first_node_uuid
from benchmarks.timing import RequestTimer

_BREAKDOWN_PATH = Path(__file__).resolve().parent.parent / '_breakdown_data.jsonl'

# ---------------------------------------------------------------------------
# Monkeypatch helpers
# ---------------------------------------------------------------------------

DB_METHODS = ('get_many', 'get_one', 'get_related_one', 'get_related_many', 'get_field')
SERIALIZE_METHODS = ('collection', 'resource')


def _wrap_descriptor(descriptor, timer, label):
    """Wrap a class-dict descriptor so calls are timed under *label*."""
    if isinstance(descriptor, classmethod):
        original = descriptor.__func__

        @functools.wraps(original)
        @classmethod
        def wrapper(cls, *args, **kwargs):
            with timer.measure(label):
                return original(cls, *args, **kwargs)

        return wrapper
    if isinstance(descriptor, staticmethod):
        original = descriptor.__func__

        @functools.wraps(original)
        @staticmethod
        def wrapper(*args, **kwargs):
            with timer.measure(label):
                return original(*args, **kwargs)

        return wrapper
    original = descriptor

    @functools.wraps(original)
    def wrapper(self, *args, **kwargs):
        with timer.measure(label):
            return original(self, *args, **kwargs)

    return wrapper


@pytest.fixture()
def timed_layers(monkeypatch):
    """Patch service and adapter methods to record timing into a shared RequestTimer."""
    from aiida_restapi.jsonapi.adapters import JsonApiAdapter
    from aiida_restapi.jsonapi.responses import JsonApiResponse
    from aiida_restapi.services.entity import EntityService

    timer = RequestTimer()

    for method_name in DB_METHODS:
        monkeypatch.setattr(
            EntityService,
            method_name,
            _wrap_descriptor(
                EntityService.__dict__[method_name],
                timer,
                f'db:{method_name}',
            ),
        )

    for method_name in SERIALIZE_METHODS:
        monkeypatch.setattr(
            JsonApiAdapter,
            method_name,
            _wrap_descriptor(
                JsonApiAdapter.__dict__[method_name],
                timer,
                f'serialize:{method_name}',
            ),
        )

    monkeypatch.setattr(
        JsonApiResponse,
        'render',
        _wrap_descriptor(
            JsonApiResponse.__dict__['render'],
            timer,
            'response:render',
        ),
    )

    yield timer


def _run_with_breakdown(client, method, url, timer, rounds=20, endpoint=None, **kwargs):
    """Run *url* for *rounds* timed requests, accumulating timing in *timer*.

    Returns per-request aggregates (means over *rounds*). Extra ``kwargs``
    (e.g. ``json=...`` for POST) are forwarded to every request so the timed
    run measures the same call the benchmark measured.
    """
    method_fn = getattr(client, method)

    for _ in range(3):
        method_fn(url, **kwargs)

    timer.clear()
    for _ in range(rounds):
        method_fn(url, **kwargs)

    resp = method_fn(url, **kwargs)
    assert resp.status_code < 500, f'{method.upper()} {url} -> {resp.status_code}'

    result = {
        'endpoint': endpoint or url,
        'method': method.upper(),
        'url': url,
        'response_bytes': len(resp.content),
        'status_code': resp.status_code,
        'rounds': rounds,
        **timer.to_dict(rounds=rounds),
    }
    with open(_BREAKDOWN_PATH, 'a') as f:
        f.write(json.dumps(result) + '\n')
    return result


# ---------------------------------------------------------------------------
# Breakdown tests
# ---------------------------------------------------------------------------


@pytest.mark.benchmark
@pytest.mark.parametrize(
    'endpoint',
    [
        '/nodes?page_size=50',
        '/computers',
        '/users',
        '/groups',
    ],
)
def test_bench_breakdown_list(benchmark, client, timed_layers, endpoint):
    """Breakdown for collection/list endpoints."""
    from benchmarks.helpers import bench_request

    bench_request(benchmark, client, 'get', endpoint)

    result = _run_with_breakdown(client, 'get', endpoint, timed_layers, rounds=20)
    print(f'\n\n--- Breakdown for GET {endpoint} (mean per request) ---')
    print(timed_layers.report(rounds=20))
    print(f'  Response size: {result["response_bytes"]:,} bytes')


@pytest.mark.benchmark
def test_bench_breakdown_node_detail(benchmark, client, timed_layers):
    """Breakdown for single-node detail endpoint."""
    from benchmarks.helpers import bench_request

    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes')
    bench_request(benchmark, client, 'get', f'/nodes/{uuid}')

    result = _run_with_breakdown(client, 'get', f'/nodes/{uuid}', timed_layers, rounds=20)
    print(f'\n\n--- Breakdown for GET /nodes/{uuid} (mean per request) ---')
    print(timed_layers.report(rounds=20))
    print(f'  Response size: {result["response_bytes"]:,} bytes')


@pytest.mark.benchmark
def test_bench_breakdown_nodes_statistics(benchmark, client, timed_layers):
    """Breakdown for the (known-slow) statistics endpoint."""
    from benchmarks.helpers import bench_request

    bench_request(benchmark, client, 'get', '/nodes/statistics')

    result = _run_with_breakdown(client, 'get', '/nodes/statistics', timed_layers, rounds=5)
    print('\n\n--- Breakdown for GET /nodes/statistics (mean per request) ---')
    print(timed_layers.report(rounds=5))
    print(f'  Response size: {result["response_bytes"]:,} bytes')


@pytest.mark.benchmark
@pytest.mark.parametrize(
    'payload',
    [
        {'path': [{'node_type': 'data.'}], 'project': ['id'], 'limit': 10},
        {'path': [{'node_type': 'data.core.int.Int.'}], 'project': ['id', 'node_type', 'ctime'], 'limit': 50},
    ],
    ids=['simple-count', 'projected-fetch'],
)
def test_bench_breakdown_querybuilder(benchmark, client, timed_layers, payload):
    """Breakdown for raw QueryBuilder POST queries."""
    from benchmarks.helpers import bench_request

    bench_request(benchmark, client, 'post', '/querybuilder', json=payload)

    result = _run_with_breakdown(client, 'post', '/querybuilder', timed_layers, rounds=20, json=payload)
    print(f'\n\n--- Breakdown for POST /querybuilder ({payload}) (mean per request) ---')
    print(timed_layers.report(rounds=20))
    print(f'  Response size: {result["response_bytes"]:,} bytes')
