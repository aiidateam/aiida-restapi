"""Test the /groups endpoint"""

from __future__ import annotations

import pytest
from aiida import orm
from fastapi.testclient import TestClient


def test_get_group_schema(client: TestClient):
    """Test retrieving the group schema."""
    response = client.get('/groups/schema')
    assert response.status_code == 200
    result = response.json()
    assert 'properties' in result
    assert sorted(result['properties'].keys()) == sorted(orm.Group.fields.keys())


def test_get_group_projections(client: TestClient):
    """Test get projections for group."""
    response = client.get('/groups/projections')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Group.fields.keys())


@pytest.mark.usefixtures('default_groups')
def test_get_groups(client: TestClient):
    """Test listing existing groups."""
    response = client.get('/groups')
    assert response.status_code == 200
    assert len(response.json()['data']) == 2


def test_get_group(client: TestClient, default_groups: list[str]):
    """Test retrieving a single group."""
    for group_id in default_groups:
        response = client.get(f'/groups/{group_id}')
        assert response.status_code == 200


def test_get_group_user(client: TestClient):
    """Test retrieving the user of a single group."""
    group = orm.Group(label='test_group_user').store()
    response = client.get(f'/groups/{group.uuid}/user')
    assert response.status_code == 200
    assert response.json()['data']['attributes']['email'] == group.user.email


def test_get_group_nodes(client: TestClient, default_nodes: list[str]):
    """Test retrieving nodes of a single group."""
    group = orm.Group(label='test_group_nodes').store()
    group.add_nodes([orm.load_node(node_id) for node_id in default_nodes])
    response = client.get(f'/groups/{group.uuid}/nodes')
    assert response.status_code == 200
    data = response.json()['data']
    returned_node_ids = {item['id'] for item in data}
    assert returned_node_ids == set(default_nodes)


def test_get_group_extras(client: TestClient):
    """Test retrieving extras of a single group."""
    group = orm.Group(label='test_group_extras').store()
    group.base.extras.set('extra_key', 'extra_value')
    response = client.get(f'/groups/{group.uuid}/extras')
    assert response.status_code == 200
    assert response.json()['data']['attributes'] == {'extra_key': 'extra_value'}


@pytest.mark.usefixtures('authenticate')
def test_create_group(client: TestClient):
    """Test creating a new group."""
    response = client.post('/groups', json={'label': 'test_label_create'})
    assert response.status_code == 200, response.content
    assert response.json()['data']['attributes']['label'] == 'test_label_create'
