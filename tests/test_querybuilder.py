"""Test the /querybuilder endpoint"""

import pytest
from aiida import orm
from fastapi.testclient import TestClient


@pytest.mark.usefixtures('default_nodes')
def test_querybuilder_all(client: TestClient):
    """Test a simple QueryBuilder request."""
    response = client.post(
        '/querybuilder',
        json={
            'path': [
                {
                    'entity_type': 'data.core.base.',
                    'orm_base': 'node',
                    'tag': 'nodes',
                },
            ],
        },
    )
    assert response.status_code == 200
    assert len(response.json()['data']['attributes']['results']) == 4


@pytest.mark.usefixtures('default_nodes')
def test_querybuilder_full(client: TestClient):
    """Test QueryBuilder result with full response."""
    response = client.post(
        '/querybuilder?flat=true&full=true',
        json={
            'path': [
                {
                    'entity_type': 'data.core.int.Int.',
                    'orm_base': 'node',
                    'tag': 'integer',
                },
            ],
        },
    )
    assert response.status_code == 200
    result = response.json()['data']['attributes']['results'][0]
    assert 'attributes' in result
    assert 'value' in result['attributes']
    assert result['attributes']['value'] == 1
    assert 'extras' in result
    assert 'repository_metadata' in result


@pytest.mark.usefixtures('default_nodes')
def test_querybuilder_flat(client: TestClient):
    """Test QueryBuilder result with flat response."""
    response = client.post(
        '/querybuilder?flat=true',
        json={
            'path': [
                {
                    'entity_type': ['data.core.int.Int.', 'data.core.float.Float.'],
                    'orm_base': 'node',
                    'tag': 'nodes',
                },
            ],
            'project': {
                'nodes': [
                    'attributes.value',
                ],
            },
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result['data']['attributes']['results'] == [1, 1.1]


def test_querybuilder_node_in_group(client: TestClient, default_nodes: list[str], default_groups: list[str]):
    """Test a QueryBuilder request filtering integers by group membership."""
    node = orm.load_node(default_nodes[0])
    group = orm.load_group(default_groups[0])
    group.add_nodes(node)
    response = client.post(
        '/querybuilder?flat=true',
        json={
            'path': [
                {
                    'entity_type': 'group.core.',
                    'orm_base': 'group',
                    'tag': 'group',
                },
                {
                    'entity_type': 'data.core.int.Int.',
                    'orm_base': 'node',
                    'joining_keyword': 'with_group',
                    'joining_value': 'group',
                    'tag': 'node',
                },
            ],
            'filters': {
                'group': {
                    'pk': group.pk,
                }
            },
            'project': {
                'group': [
                    'label',
                ],
                'node': [
                    'pk',
                    'attributes.value',
                ],
            },
        },
    )
    assert response.status_code == 200
    result = response.json()['data']['attributes']['results']
    assert result == [group.label, node.pk, node.value]
