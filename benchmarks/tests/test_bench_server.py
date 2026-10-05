"""Benchmarks for /server endpoints."""

import pytest

from benchmarks.helpers import bench_request as _bench


@pytest.mark.benchmark
def test_bench_server_info(benchmark, client):
    _bench(benchmark, client, 'get', '/server/info')


@pytest.mark.benchmark
def test_bench_server_endpoints(benchmark, client):
    _bench(benchmark, client, 'get', '/server/endpoints')
