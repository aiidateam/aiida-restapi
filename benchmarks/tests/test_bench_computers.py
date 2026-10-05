"""Benchmarks for /computers endpoints."""

import pytest
from aiida import orm

from benchmarks.helpers import bench_request as _bench
from benchmarks.helpers import first_pk


def _first_computer_pk():
    return first_pk(orm.Computer)


@pytest.mark.benchmark
def test_bench_computers_list(benchmark, client):
    _bench(benchmark, client, 'get', '/computers')


@pytest.mark.benchmark
def test_bench_computers_schema(benchmark, client):
    _bench(benchmark, client, 'get', '/computers/schema')


@pytest.mark.benchmark
def test_bench_computers_projections(benchmark, client):
    _bench(benchmark, client, 'get', '/computers/projections')


@pytest.mark.benchmark
def test_bench_computer_detail(benchmark, client):
    pk = _first_computer_pk()
    if pk is None:
        pytest.skip('no computers in profile')
    _bench(benchmark, client, 'get', f'/computers/{pk}')


@pytest.mark.benchmark
def test_bench_computer_metadata(benchmark, client):
    pk = _first_computer_pk()
    if pk is None:
        pytest.skip('no computers in profile')
    _bench(benchmark, client, 'get', f'/computers/{pk}/metadata')
