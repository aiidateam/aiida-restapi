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
            'project': {
                'nodes': [
                    'attributes.value',
                ],
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data['data']) == 4


@pytest.mark.usefixtures('default_nodes')
def test_querybuilder_numeric_flat(client: TestClient):
    """Test a simple QueryBuilder request."""
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
    data = response.json()
    assert data['data'] == [1, 1.1]


def test_querybuilder_integer_in_group(client: TestClient, default_nodes: list[str], default_groups: list[str]):
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
    data = response.json()
    assert data['data'] == [group.label, node.pk, node.value]
