"""Benchmarks for /users endpoints."""

import pytest
from aiida import orm


def _first_user_pk():
    pk = orm.QueryBuilder().append(orm.User, project=['pk']).first()
    return pk[0] if pk else None


@pytest.mark.benchmark
def test_bench_users_list(benchmark, client):
    benchmark(client.get, '/users')


@pytest.mark.benchmark
def test_bench_users_schema(benchmark, client):
    benchmark(client.get, '/users/schema')


@pytest.mark.benchmark
def test_bench_users_projections(benchmark, client):
    benchmark(client.get, '/users/projections')


@pytest.mark.benchmark
def test_bench_user_detail(benchmark, client):
    pk = _first_user_pk()
    if pk is None:
        pytest.skip('no users in profile')
    benchmark(client.get, f'/users/{pk}')
