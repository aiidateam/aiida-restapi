"""Benchmarks for /users endpoints."""

import pytest
from aiida import orm

from benchmarks.helpers import bench_request as _bench
from benchmarks.helpers import first_pk


def _first_user_pk():
    return first_pk(orm.User)


@pytest.mark.benchmark
def test_bench_users_list(benchmark, client):
    _bench(benchmark, client, 'get', '/users')


@pytest.mark.benchmark
def test_bench_users_schema(benchmark, client):
    _bench(benchmark, client, 'get', '/users/schema')


@pytest.mark.benchmark
def test_bench_users_projections(benchmark, client):
    _bench(benchmark, client, 'get', '/users/projections')


@pytest.mark.benchmark
def test_bench_user_detail(benchmark, client):
    pk = _first_user_pk()
    if pk is None:
        pytest.skip('no users in profile')
    _bench(benchmark, client, 'get', f'/users/{pk}')
