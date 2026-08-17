"""Benchmark breakdown: measures where time is spent per request.

Instead of only measuring total request latency, this test instruments
the internal layers (DB query, JSON:API serialization) so you can see
the percentage split.

Run with:
    pytest benchmarks/tests/test_bench_breakdown.py --benchmark-enable -v -s
"""

import functools
import json
from pathlib import Path

import pytest

from benchmarks.timing import RequestTimer

_BREAKDOWN_PATH = Path(__file__).resolve().parent.parent / '_breakdown_data.jsonl'

# ---------------------------------------------------------------------------
# Monkeypatch helpers
# ---------------------------------------------------------------------------

class _MethodWrapper:
    """Descriptor that wraps a method and records timing, preserving binding."""

    def __init__(self, original, timer, label):
        self._original = original
        self._timer = timer
        self._label = label

    def __get__(self, obj, objtype=None):
        if obj is None:
            raw = self._original

            @functools.wraps(raw)
            def bound_cls_wrapper(*args, **kwargs):
                with self._timer.measure(self._label):
                    return raw(objtype, *args, **kwargs)

            return bound_cls_wrapper
        bound = self._original.__get__(obj, objtype)

        @functools.wraps(self._original)
        def instance_wrapper(*args, **kwargs):
            with self._timer.measure(self._label):
                return bound(*args, **kwargs)

        return instance_wrapper


def _get_unbound(cls, name):
    """Get the raw function from a class, handling classmethods."""
    attr = cls.__dict__[name]
    if isinstance(attr, classmethod):
        return attr.__func__
    return attr


@pytest.fixture()
def timed_layers(monkeypatch):
    """Patch service and adapter methods to record timing into a shared RequestTimer."""
    from aiida_restapi.jsonapi.adapters import JsonApiAdapter
    from aiida_restapi.jsonapi.responses import JsonApiResponse
    from aiida_restapi.services.entity import EntityService

    timer = RequestTimer()

    for method_name in ('get_many', 'get_one', 'get_related_one', 'get_related_many', 'get_field'):
        original = getattr(EntityService, method_name)
        monkeypatch.setattr(
            EntityService,
            method_name,
            _MethodWrapper(original, timer, 'db_query'),
        )

    for method_name in ('collection', 'resource'):
        raw_fn = _get_unbound(JsonApiAdapter, method_name)
        monkeypatch.setattr(
            JsonApiAdapter,
            method_name,
            _MethodWrapper(raw_fn, timer, 'jsonapi_serialize'),
        )

    original = getattr(JsonApiResponse, 'render')
    monkeypatch.setattr(
        JsonApiResponse,
        'render',
        _MethodWrapper(original, timer, 'response_render'),
    )

    yield timer


def _run_with_breakdown(client, method, url, timer, rounds=20, endpoint=None):
    """Run *url* for *rounds* iterations, accumulating timing in *timer*."""
    method_fn = getattr(client, method)

    for _ in range(3):
        method_fn(url)

    timer.clear()
    for _ in range(rounds):
        method_fn(url)

    resp = method_fn(url)
    size = len(resp.content)

    result = {
        'endpoint': endpoint or url,
        'method': method.upper(),
        'url': url,
        'response_bytes': size,
        'status_code': resp.status_code,
        'rounds': rounds,
        **timer.to_dict(),
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
    resp = client.get(endpoint)
    benchmark.extra_info['response_bytes'] = len(resp.content)

    def _request():
        client.get(endpoint)

    benchmark(_request)

    result = _run_with_breakdown(client, 'get', endpoint, timed_layers, rounds=20)
    print(f'\n\n--- Breakdown for GET {endpoint} ---')
    print(timed_layers.report())
    print(f'  Response size: {result["response_bytes"]:,} bytes')


@pytest.mark.benchmark
def test_bench_breakdown_node_detail(benchmark, client, timed_layers):
    """Breakdown for single-node detail endpoint."""
    from aiida import orm

    row = orm.QueryBuilder().append(orm.Node, project=['uuid']).first()
    if row is None:
        pytest.skip('no nodes')
    uuid = row[0]
    resp = client.get(f'/nodes/{uuid}')
    benchmark.extra_info['response_bytes'] = len(resp.content)

    def _request():
        client.get(f'/nodes/{uuid}')

    benchmark(_request)

    result = _run_with_breakdown(client, 'get', f'/nodes/{uuid}', timed_layers, rounds=20)
    print(f'\n\n--- Breakdown for GET /nodes/{uuid} ---')
    print(timed_layers.report())
    print(f'  Response size: {result["response_bytes"]:,} bytes')


@pytest.mark.benchmark
def test_bench_breakdown_nodes_statistics(benchmark, client, timed_layers):
    """Breakdown for the (known-slow) statistics endpoint."""
    resp = client.get('/nodes/statistics')
    benchmark.extra_info['response_bytes'] = len(resp.content)

    def _request():
        client.get('/nodes/statistics')

    benchmark(_request)

    result = _run_with_breakdown(client, 'get', '/nodes/statistics', timed_layers, rounds=5)
    print('\n\n--- Breakdown for GET /nodes/statistics ---')
    print(timed_layers.report())
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
    resp = client.post('/querybuilder', json=payload)
    benchmark.extra_info['response_bytes'] = len(resp.content)

    def _request():
        client.post('/querybuilder', json=payload)

    benchmark(_request)

    result = _run_with_breakdown(client, 'post', '/querybuilder', timed_layers, rounds=20)
    print(f'\n\n--- Breakdown for POST /querybuilder ({payload}) ---')
    print(timed_layers.report())
    print(f'  Response size: {result["response_bytes"]:,} bytes')
