"""Test the /computers endpoint"""

from __future__ import annotations

import pytest
from aiida import orm
from fastapi.testclient import TestClient


def test_get_computer_projectable_properties(client: TestClient):
    """Test get projectable properties for computer."""
    response = client.get('/computers/projectable_properties')
    assert response.status_code == 200
    assert response.json() == sorted(orm.Computer.fields.keys())


@pytest.mark.usefixtures('default_computers')
def test_get_computers(client: TestClient):
    """Test listing existing computer."""
    response = client.get('/computers/')
    assert response.status_code == 200
    assert len(response.json()['results']) == 2


def test_get_computer(client: TestClient, default_computers: list[int | None]):
    """Test retrieving a single computer."""
    for comp_id in default_computers:
        response = client.get(f'/computers/{comp_id}')
        assert response.status_code == 200


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
    computers = [comp['label'] for comp in response.json()['results']]
    assert 'test_comp' in computers
