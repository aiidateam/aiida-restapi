"""Benchmarks for /nodes endpoints."""

import pytest

from benchmarks.helpers import bench_request as _bench
from benchmarks.helpers import first_data_node_uuid, first_node_uuid

# -- collection --------------------------------------------------------------


@pytest.mark.benchmark
def test_bench_nodes_list(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes')


@pytest.mark.benchmark
def test_bench_nodes_list_page_10(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes?page_size=10')


@pytest.mark.benchmark
def test_bench_nodes_list_page_100(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes?page_size=100')


# -- schema / projections / metadata ----------------------------------------


@pytest.mark.benchmark
def test_bench_nodes_schema(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes/schema')


@pytest.mark.benchmark
def test_bench_nodes_projections(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes/projections')


@pytest.mark.benchmark
def test_bench_nodes_statistics(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes/statistics')


@pytest.mark.benchmark
def test_bench_nodes_types(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes/types')


@pytest.mark.benchmark
def test_bench_nodes_download_formats(benchmark, client):
    _bench(benchmark, client, 'get', '/nodes/download_formats')


# -- single node detail pages ------------------------------------------------


@pytest.mark.benchmark
def test_bench_node_detail(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}')


@pytest.mark.benchmark
def test_bench_node_user(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/user')


@pytest.mark.benchmark
def test_bench_node_computer(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/computer')


@pytest.mark.benchmark
def test_bench_node_groups(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/groups')


@pytest.mark.benchmark
def test_bench_node_attributes(benchmark, client):
    uuid = first_data_node_uuid() or first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/attributes')


@pytest.mark.benchmark
def test_bench_node_extras(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/extras')


@pytest.mark.benchmark
def test_bench_node_links(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/links')


@pytest.mark.benchmark
def test_bench_node_repo_metadata(benchmark, client):
    uuid = first_node_uuid()
    if uuid is None:
        pytest.skip('no nodes in profile')
    _bench(benchmark, client, 'get', f'/nodes/{uuid}/repo/metadata')
