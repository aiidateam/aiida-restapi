"""Benchmarks for /graphql endpoint."""

import pytest


@pytest.mark.benchmark
def test_bench_graphql_all_nodes(benchmark, client):
    query = '{ aiida { nodes { totalCount edges { node { uuid nodeType } } } } }'
    benchmark(client.post, '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_users(benchmark, client):
    query = '{ aiida { users { totalCount edges { node { pk email } } } } }'
    benchmark(client.post, '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_computers(benchmark, client):
    query = '{ aiida { computers { totalCount edges { node { pk label } } } } }'
    benchmark(client.post, '/graphql', json={'query': query})


@pytest.mark.benchmark
def test_bench_graphql_groups(benchmark, client):
    query = '{ aiida { groups { totalCount edges { node { uuid label } } } } }'
    benchmark(client.post, '/graphql', json={'query': query})
