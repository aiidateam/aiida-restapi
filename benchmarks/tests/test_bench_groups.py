"""Benchmarks for /groups endpoints."""

import pytest
from aiida import orm

from benchmarks.helpers import bench_request as _bench
from benchmarks.helpers import first_uuid


def _first_group_uuid():
    return first_uuid(orm.Group)


@pytest.mark.benchmark
def test_bench_groups_list(benchmark, client):
    _bench(benchmark, client, 'get', '/groups')


@pytest.mark.benchmark
def test_bench_groups_schema(benchmark, client):
    _bench(benchmark, client, 'get', '/groups/schema')


@pytest.mark.benchmark
def test_bench_groups_projections(benchmark, client):
    _bench(benchmark, client, 'get', '/groups/projections')


@pytest.mark.benchmark
def test_bench_group_detail(benchmark, client):
    uuid = _first_group_uuid()
    if uuid is None:
        pytest.skip('no groups in profile')
    _bench(benchmark, client, 'get', f'/groups/{uuid}')


@pytest.mark.benchmark
def test_bench_group_user(benchmark, client):
    uuid = _first_group_uuid()
    if uuid is None:
        pytest.skip('no groups in profile')
    _bench(benchmark, client, 'get', f'/groups/{uuid}/user')


@pytest.mark.benchmark
def test_bench_group_nodes(benchmark, client):
    uuid = _first_group_uuid()
    if uuid is None:
        pytest.skip('no groups in profile')
    _bench(benchmark, client, 'get', f'/groups/{uuid}/nodes')
