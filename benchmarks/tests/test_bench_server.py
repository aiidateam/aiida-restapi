"""Benchmarks for /server endpoints."""

import pytest


@pytest.mark.benchmark
def test_bench_server_info(benchmark, client):
    benchmark(client.get, '/server/info')


@pytest.mark.benchmark
def test_bench_server_endpoints(benchmark, client):
    benchmark(client.get, '/server/endpoints')
