"""Benchmarks for /graphql endpoint."""

import pytest

from benchmarks.tests.conftest import _bench


@pytest.mark.benchmark
def test_bench_graphql_all_nodes(benchmark, client):
    query = '{ aiida { nodes { totalCount edges { node { uuid nodeType } } } } }'
    _bench(benchmark, client, 'post', '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_users(benchmark, client):
    query = '{ aiida { users { totalCount edges { node { pk email } } } } }'
    _bench(benchmark, client, 'post', '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_computers(benchmark, client):
    query = '{ aiida { computers { totalCount edges { node { pk label } } } } }'
    _bench(benchmark, client, 'post', '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_groups(benchmark, client):
    query = '{ aiida { groups { totalCount edges { node { uuid label } } } } }'
    _bench(benchmark, client, 'post', '/graphql', json={'query': query})
