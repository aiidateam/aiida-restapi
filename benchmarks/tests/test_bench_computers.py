"""Benchmarks for /computers endpoints."""

import pytest
from aiida import orm


def _first_computer_pk():
    pk = orm.QueryBuilder().append(orm.Computer, project=['pk']).first()
    return pk[0] if pk else None


@pytest.mark.benchmark
def test_bench_computers_list(benchmark, client):
    benchmark(client.get, '/computers')


@pytest.mark.benchmark
def test_bench_computers_schema(benchmark, client):
    benchmark(client.get, '/computers/schema')


@pytest.mark.benchmark
def test_bench_computers_projections(benchmark, client):
    benchmark(client.get, '/computers/projections')


@pytest.mark.benchmark
def test_bench_computer_detail(benchmark, client):
    pk = _first_computer_pk()
    if pk is None:
        pytest.skip('no computers in profile')
    benchmark(client.get, f'/computers/{pk}')


@pytest.mark.benchmark
def test_bench_computer_metadata(benchmark, client):
    pk = _first_computer_pk()
    if pk is None:
        pytest.skip('no computers in profile')
    benchmark(client.get, f'/computers/{pk}/metadata')
