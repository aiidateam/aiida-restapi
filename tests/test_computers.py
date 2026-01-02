"""Test the /computers endpoint"""

from __future__ import annotations

import pytest
from aiida import orm
from fastapi.testclient import TestClient


def test_get_computer_schema(client: TestClient):
    """Test retrieving the computer schema."""
    response = client.get('/computers/schema')
    assert response.status_code == 200
    result = response.json()
    assert 'properties' in result
    assert sorted(result['properties'].keys()) == sorted(orm.Computer.fields.keys())


def test_get_computer_projections(client: TestClient):
    """Test get projections for computer."""
    response = client.get('/computers/projections')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Computer.fields.keys())


@pytest.mark.usefixtures('default_computers')
def test_get_computers(client: TestClient):
    """Test listing existing computer."""
    response = client.get('/computers/')
    assert response.status_code == 200
    assert len(response.json()['data']) == 2


def test_get_computer(client: TestClient, default_computers: list[int | None]):
    """Test retrieving a single computer."""
    for comp_id in default_computers:
        response = client.get(f'/computers/{comp_id}')
        assert response.status_code == 200


def test_get_computer_metadata(client: TestClient):
    metadata = {
        'workdir': '/tmp/aiida',
        'minimum_scheduler_poll_interval': 15,
        'default_mpiprocs_per_machine': 2,
    }
    computer = orm.Computer(
        label='meta_comp',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.direct',
        metadata=metadata,
    ).store()

    response = client.get(f'/computers/{computer.pk}/metadata')
    assert response.status_code == 200
    data = response.json()
    assert data == metadata
    orm.Computer.collection.delete(computer.pk)


@pytest.mark.usefixtures('authenticate')
def test_create_computer(client: TestClient):
    """Test creating a new computer."""
    response = client.post(
        '/computers',
        json={
            'label': 'test_comp',
            'hostname': 'fake_host',
            'transport_type': 'core.local',
            'scheduler_type': 'core.pbspro',
        },
    )
    assert response.status_code == 200, response.content
    response = client.get('/computers')
    computers = [comp['label'] for comp in response.json()['data']]
    assert 'test_comp' in computers
