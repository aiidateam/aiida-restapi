"""Benchmarks for /querybuilder endpoint."""

import pytest

from benchmarks.tests.conftest import _bench


@pytest.mark.benchmark
def test_bench_qb_count_nodes(benchmark, client):
    """Count all nodes."""
    payload = {
        'path': [{'node_type': 'data.core.int.Int.'}],
        'project': ['id'],
    }
    _bench(benchmark, client, 'post', '/querybuilder', json=payload)


@pytest.mark.benchmark
def test_bench_qb_fetch_first_10(benchmark, client):
    """Fetch first 10 node PKs."""
    payload = {
        'path': [{'node_type': 'data.'}],
        'project': ['id', 'node_type', 'ctime'],
        'limit': 10,
    }
    _bench(benchmark, client, 'post', '/querybuilder', json=payload)


@pytest.mark.benchmark
def test_bench_qb_filter_by_type(benchmark, client):
    """Fetch nodes filtered by type with projections."""
    payload = {
        'path': [{'node_type': 'data.core.dict.Dict.'}],
        'project': ['id', 'attributes'],
        'limit': 20,
    }
    _bench(benchmark, client, 'post', '/querybuilder', json=payload)


@pytest.mark.benchmark
def test_bench_qb_with_joins(benchmark, client):
    """Query nodes joined with their computer."""
    payload = {
        'path': [
            {'node_type': 'process.calculation.calcjob.CalcJobNode.'},
            {'computer': {'with_incoming': 'node[0]'}},
        ],
        'project': ['node[0].id', 'node[0].node_type', 'computer.label'],
        'limit': 10,
    }
    _bench(benchmark, client, 'post', '/querybuilder', json=payload)
